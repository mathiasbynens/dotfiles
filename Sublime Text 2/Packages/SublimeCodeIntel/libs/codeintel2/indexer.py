#!python
# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
# 
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
# 
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
# License for the specific language governing rights and limitations
# under the License.
# 
# The Original Code is Komodo code.
# 
# The Initial Developer of the Original Code is ActiveState Software Inc.
# Portions created by ActiveState Software Inc are Copyright (C) 2000-2007
# ActiveState Software Inc. All Rights Reserved.
# 
# Contributor(s):
#   ActiveState Software Inc
# 
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
# 
# ***** END LICENSE BLOCK *****

"""The codeintel indexer is a thread that handles scanning files and
loading them into the database. There is generally one indexer on the
Manager instance.

    mgr.idxr = Indexer(mgr)

XXX A separate indexer instance may be used for batch updates of the db.
"""
# TODO:
# - How are scan errors handled? do we try to keep from re-scanning over
#   and over? Perhaps still use mtime to only try again on new content.
#   Could still have a "N strikes in the last 1 minute" rule or
#   something.
# - batch updating (still wanted? probably)

import os, sys
import threading
import time
import bisect
import Queue
from hashlib import md5
import traceback

import logging

from codeintel2.common import *
from codeintel2.buffer import Buffer
from codeintel2.database.langlib import LangDirsLib
from codeintel2.database.multilanglib import MultiLangDirsLib

if _xpcom_:
    from xpcom.server import UnwrapObject



#---- globals

log = logging.getLogger("codeintel.indexer")
#log.setLevel(logging.DEBUG)



#---- internal support

class _PriorityQueue(Queue.Queue):
    """A thread-safe priority queue.
    
    In order to use this the inserted items should be tuples with the
    priority first. Note that subsequent elements of the item tuples will
    be used for secondary sorting. As a result, it is often desirable to
    make the second tuple index be a timestamp so that the queue is a
    FIFO for elements with the same priority, e.g.:
        item = (PRIORITY, time.time(), element)
        
    Usage:
        q = _PriorityQueue(0)  # unbounded queue
        q.put( (2, time.time(), "second") )
        q.put( (1, time.time(), "first") )
        q.put( (3, time.time(), "third") )
        priority, timestamp, value = q.get()
    """
    def _put(self, item):
        bisect.insort(self.queue, item)

    # The following are to ensure a *list* is being used as the internal
    # Queue data structure. Python 2.4 switched to using a deque
    # internally which doesn't have the insert() method that
    # bisect.insort() uses.
    def _init(self, maxsize):
        self.maxsize = maxsize
        self.queue = []
    def _get(self):
        return self.queue.pop(0)


class _Request(object):
    """Base class for a queue-able thing.
    
    A request object must have an 'id'. This is used for "staging"
    requests on the queue. A staged request will sit around for 'delay'
    amount of time before actually being put on the processing queue.
    During that wait, a subsequent stage request with the same 'id' will
    replace the first one -- including resetting the delay. This is
    useful for staging relatively expensive processing in the background
    for content that is under ongoing changes (e.g. for processing an
    editor buffer while it is being editted).
    """
    #XXX PERF: use a slot?
    id = None
    def __init__(self, id=None):
        if id is not None:
            self.id = id


class _UniqueRequestPriorityQueue(_PriorityQueue):
    """A thread-safe priority queue for '_Request' objects.
    
    This queue class extends _PriorityQueue with the condition that:
    When adding a _Request to the queue, if a _Request with the same id
    already exists in the queue, then the new _Request inherits the
    higher priority and the earlier timestamp of the two and _replaces_
    the older _Request.

    This condition is added because there is no point in scanning file
    contents from time T1 when a scan of the file contents at time T2
    (more recent) is being requested. It is important to adopt the
    higher priority (and earlier timestamp) to ensure the requestor does
    not starve.

    Note: This presumes that an "item" is this 3-tuple:
        (<priority-number>, <timestamp>, <_Request instance>)
    """
    def __init__(self, maxsize=0):
        _PriorityQueue.__init__(self, maxsize)
        self._item_from_id = {}

    def _put(self, item):
        # Remove a possible existing request for the same file (there can
        # be only one).
        priority, timestamp, request = item
        id = request.id
        if id in self._item_from_id:
            i = self._item_from_id[id]
            self.queue.remove(i)
            p, t, r = i
            item = (min(priority, p), t, request)
        # Add the (possibly updated) item to the queue.
        self._item_from_id[id] = item
        _PriorityQueue._put(self, item)

    def _get(self):
        item = _PriorityQueue._get(self)
        del self._item_from_id[item[-1].id]
        return item


class _StagingRequestQueue(_UniqueRequestPriorityQueue):
    """A thread-safe priority queue for '_Request' objects with delayed
    staging support.
    
    This queue class extends _UniqueRequestPriorityQueue by adding the
    .stage() method. This method is like the regular .put() method
    except that staged requests are only actually placed on the queue if
    a certain period of inactivity passes without subsequent stage
    requests for the same request id.

    This is to support reasonable performance for live updating while a
    document is being edited. Rather than executing a scan for every
    intermediate edited state, scanning is only  after a period of
    relative inactivity.
    
    One additional burden is that a "staging thread" is involved so one must
    call this queue's .finalize() method to properly shut it down.
    
    As with the _ScanRequestQueue this queue presumes that and item is this
    3-tuple:
            (<priority-number>, <timestamp>, <ScanRequest instance>)
    """
    DEFAULT_STAGING_DELAY = 1.5 # default delay from on deck -> on queue (s)

    def __init__(self, maxsize=0, stagingDelay=None):
        """Create a staging scan request queue.
        
            "maxsize" (optional) is an upperbound limit on the number of
                items in the queue (<= 0 means the queue is unbounded).
            "stagingDelay" (optional) is a number of seconds to use as a
                delay from being staged to being placed on the queue.
        """
        _UniqueRequestPriorityQueue.__init__(self, maxsize)
        if stagingDelay is None:
            self._stagingDelay = self.DEFAULT_STAGING_DELAY
        else:
            self._stagingDelay = stagingDelay
        self._onDeck = {
            # <request-id> : (<time when due>, <priority>, <queue item>)
        }
        self._nothingOnDeck = threading.Lock()
        self._nothingOnDeck.acquire()
        self._terminate = 0 # boolean telling "staging thread" to terminate
        self._stager = threading.Thread(target=self._stagingThread,
                                        name="request staging thread")
        self._stager.setDaemon(True)
        self._stager.start()

    def finalize(self):
        if self._stager:
            self._terminate = 1
            # Make sure staging thread isn't blocked so it can terminate.
            self.mutex.acquire()
            try:
                if not self._onDeck:
                    self._nothingOnDeck.release()
            finally:
                self.mutex.release()
            # Don't bother join'ing because there is no point waiting for
            # up to self._stagingDelay while the staging thread shuts down.
            #self._stager.join()

    def stage(self, item, delay=None):
        if delay is None:
            delay = self._stagingDelay
        self.mutex.acquire()
        try:
            priority, timestamp, request = item
            wasEmpty = not self._onDeck
            if request.id not in self._onDeck \
               or self._onDeck[request.id][1] != PRIORITY_IMMEDIATE:
                self._onDeck[request.id] = (timestamp + delay, priority, item)
                if wasEmpty:
                    self._nothingOnDeck.release()
        finally:
            self.mutex.release()

    def _stagingThread(self):
        """Thread that handles moving requests on-deck to the queue."""
        log.debug("staging thread: start")
        while 1:
            # If nothing is on-deck, wait until there is.
            #log.debug("staging thread: acquire self._nothingOnDeck")
            self._nothingOnDeck.acquire()
            #log.debug("staging thread: acquired self._nothingOnDeck")
            if self._terminate:
                break

            # Place any "due" items on the queue.
            self.mutex.acquire()
            somethingStillOnDeck = 1
            currTime = time.time()
            toQueue = []
            try:
                for id, (timeDue, priority, item) in self._onDeck.items():
                    if currTime >= timeDue:
                        toQueue.append(item)
                        del self._onDeck[id]
                if not self._onDeck:
                    somethingStillOnDeck = 0
            finally:
                if somethingStillOnDeck:
                    self._nothingOnDeck.release()
                self.mutex.release()
            if toQueue:
                log.debug("staging thread: queuing %r", toQueue)
                for item in toQueue:
                    self.put(item)

            # Sleep for a bit.
            #XXX If the latency it too large we may want to sleep for some
            #    fraction of the staging delay.
            log.debug("staging thread: sleep for %.3fs", self._stagingDelay)
            time.sleep(self._stagingDelay)
        log.debug("staging thread: end")



#---- public classes

class XMLParseRequest(_Request):
    """A request to re-parse and XML-y/HTML-y file

    (For XML completion and Komodo's DOMViewer.)
    """
    def __init__(self, buf, priority, force=False):
        if _xpcom_:
            buf = UnwrapObject(buf)
        self.buf = buf
        self.id = buf.path + "#xml-parse"
        self.priority = priority
        self.force = force
    def __repr__(self):
        return "<XMLParseRequest %r>" % self.id
    def __str__(self):
        return "xml parse '%s' (prio %s)" % (self.buf.path, self.priority)


class ScanRequest(_Request):
    """A request to scan a file for codeintel.
    
    A ScanRequest has the following properties:
        "buf" is the CitadelBuffer instance.
        "priority" must be one of the PRIORITY_* priorities.
        "force" is a boolean indicating if a scan should be run even if
            the database is already up-to-date for this content.
        "mtime" is the modified time of the file/content. If not given
            it defaults to the current time.
        "on_complete" (optional) is a callable to call when the scan
            and load is complete. (XXX: Is this being used by anyone?)

        "status" is set on completion. See .complete() docstring for details.
    """
    status = None
    def __init__(self, buf, priority, force=False, mtime=None, on_complete=None):
        if _xpcom_:
            buf = UnwrapObject(buf)
        self.buf = buf
        self.id = buf.path
        self.priority = priority
        self.force = force
        if mtime is None:
            self.mtime = time.time()
        else:
            self.mtime = mtime
        self.on_complete = on_complete
        self.complete_event = threading.Event() #XXX use a pool
    def __repr__(self):
        return "<ScanRequest %r>" % self.id
    def __str__(self):
        return "scan request '%s' (prio %s)" % (self.buf.path, self.priority)
    def complete(self, status):
        """Called by scheduler when this scan is complete (whether or
        not it was successful/skipped/whatever).

            "status" is one of the following:
                changed     The scan was done and (presumably) something
                            changed. PERF: Eventually want to be able to
                            detect when an actual change is made to be
                            used elsewhere to know not to update.
                skipped     The scan was skipped.
        """
        log.debug("complete %s", self)
        self.status = status
        self.complete_event.set()
        if self.on_complete:
            try:
                self.on_complete()
            except:
                log.exception("ignoring exception in ScanRequest "
                              "on_complete callback")
    def wait(self, timeout=None):
        """Can be called by code requesting a scan to wait for completion
        of this particular scan.
        """
        self.complete_event.wait(timeout)


class PreloadBufLibsRequest(_Request):
    priority = PRIORITY_BACKGROUND    
    def __init__(self, buf):
        if _xpcom_:
            buf = UnwrapObject(buf)
        self.buf = buf
        self.id = buf.path + "#preload-libs"
    def __repr__(self):
        return "<PreloadBufLibsRequest %r>" % self.id
    def __str__(self):
        return "pre-load libs for '%s'" % self.buf.path

class PreloadLibRequest(_Request):
    priority = PRIORITY_BACKGROUND    
    def __init__(self, lib):
        self.lib = lib
        self.id = "%s %s with %s dirs#preload-lib" \
                  % (lib.lang, lib.name, len(lib.dirs))
    def __repr__(self):
        return "<PreloadLibRequest %r>" % self.id
    def __str__(self):
        return "pre-load %s %s (%d dirs)" \
               % (self.lib.lang, self.lib.name, len(self.lib.dirs))


class IndexerStopRequest(_Request):
    id = "indexer stop request"
    priority = PRIORITY_CONTROL
    def __repr__(self):
        return '<'+self.id+'>'

class IndexerPauseRequest(_Request):
    id = "indexer pause request"
    priority = PRIORITY_CONTROL
    def __repr__(self):
        return '<'+self.id+'>'


class Indexer(threading.Thread):
    """A codeintel indexer thread.

    An indexer is mainly responsible for taking requests to scan
    (Citadel) buffers and load the data into the appropriate LangZone of
    the database.

#XXX Only needed when/if batch updating is redone.
##    This thread manages a queue of ScanRequest's, scheduling the scans in
##    priority order. It has two modes of usage:
##        MODE_DAEMON
##            The scheduler remains running until it is explicitly stopped with
##            the .stop() method.
##        MODE_ONE_SHOT
##            All added requests are processed and then the scheduler
##            terminates. Note that the .stageRequest() method is not
##            allowed in this mode.

    Usage:
        from codeintel.indexer import Indexer
        idxr = Indexer(mgr)
        idxr.start()
        try:
            # idxr.stage_request(<request>)
            # idxr.add_request(<request>)
        finally:
            idxr.finalize()

    Dev Notes:
    - The intention is the indexer will grow to handle other requests as
      well (saving and culling cached parts of the database).
    - There is a potential race condition on request id generation
      if addRequest/stageRequest calls are made from multiple threads.
    """
    MODE_DAEMON, MODE_ONE_SHOT = range(2)
    mode = MODE_DAEMON

    class StopIndexing(Exception):
        """Used to signal that indexer iteration should stop.

        Dev Note: I *could* use StopIteration here, but I don't want to
        possibly misinterpret a real StopIteration.
        """
        pass

    def __init__(self, mgr, on_scan_complete=None):
        """
            "on_scan_complete" (optional), if specified, is called when
                a ScanRequest is completed.

        TODO: add back the requestStartCB and completedCB (for batch updates)
        """
        threading.Thread.__init__(self, name="codeintel indexer")
        self.setDaemon(True)
        self.mgr = mgr 
        self.on_scan_complete = on_scan_complete
        if self.mode == self.MODE_DAEMON:
            self._requests = _StagingRequestQueue()
        else:
            self._requests = _UniqueRequestPriorityQueue()
        self._stopping = False
        self._resumeEvent = None

    def finalize(self):
        """Shutdown the indexer.
        
        This must be done even if the the indexer thread was never
        .start()'ed -- because of the thread used for the
        _StagingRequestQueue.
        """
        self._stopping = True
        if isinstance(self._requests, _StagingRequestQueue):
            self._requests.finalize()
        if self.isAlive():
            self.add_request(IndexerStopRequest())
            try:
                self.join(5) # see bug 77284
            except AssertionError:
                pass # thread was not started

    def pause(self):
        self._resumeEvent = threading.Event()
        self._pauseEvent = threading.Event()
        #TODO: shouldn't this be `self.add_request`?
        self.addRequest(IndexerPauseRequest())
        self._pauseEvent.wait() # wait until the Scheduler is actually paused
        log.debug("indexer: paused")

    def resume(self):
        if self._resumeEvent:
            self._resumeEvent.set()
            self._resumeEvent = None
        log.debug("indexer: resumed")

    def stage_request(self, request, delay=None):
        log.debug("stage %r", request)
        if self.mode == self.MODE_ONE_SHOT:
            raise CodeIntelError("cannot call stage requests on a "
                                 "MODE_ONE_SHOT indexer")
        #self._abortMatchingRunner(request.buf.path, request.buf.lang)
        self._requests.stage( (request.priority, time.time(), request), delay )
    def add_request(self, request):
        log.debug("add %r", request)
        #self._abortMatchingRunner(request.buf.path, request.buf.lang)
        self._requests.put( (request.priority, time.time(), request) )

#XXX re-instate for batch updating (was getNumRequests)
##    def num_requests(self):
##        return self._requests.qsize()

    def run(self):    # the scheduler thread run-time
        log.debug("indexer: start")
##        reason = "failed"
        try:
            while 1:
                try:
                    self._iteration()
                except Queue.Empty: # for mode=MODE_ONE_SHOT only
##                    reason = "completed"
                    break
                except self.StopIndexing:
##                    reason = "stopped"
                    break
                except:
                    # Because we aren't fully waiting for indexer
                    # termination in `self.finalize` it is possible that
                    # an ongoing request fails (Manager finalization
                    # destroys the `mgr.db` instance). Don't bother
                    # logging an error if we are stopping.
                    #
                    # Note: The typical culprit is a *long*
                    # <PreloadBufLibsRequest> for a PHP or JS library
                    # dir. Ideally this would be split into a number of
                    # lower-prio indexer requests.
                    if not self._stopping:
                        log.exception("unexpected internal error in indexer: "
                                      "ignoring and continuing")
        finally:
##            try:
##                if self._completedCB:
##                    self._completedCB(reason)
##            except:
##                log.exception("unexpected error in completion callback")
            log.debug("indexer thread: stopped")

    def _iteration(self):
        """Handle one request on the queue.
        
        Raises StopIndexing exception if iteration should stop.
        """
        #log.debug("indexer: get request")
        if self.mode == self.MODE_DAEMON:
            priority, timestamp, request = self._requests.get()
        else: # mode == self.MODE_ONE_SHOT
            priority, timestamp, request = self._requests.get_nowait()
        #log.debug("indexer: GOT request")

        try:
            if request.priority == PRIORITY_CONTROL: # sentinel
                if isinstance(request, IndexerStopRequest):
                    raise self.StopIndexing()
                elif isinstance(request, IndexerPauseRequest):
                    self._pauseEvent.set() # tell .pause() that Indexer has paused
                    self._resumeEvent.wait()
                    return
                else:
                    raise CodeIntelError("unexpected indexer control "
                                         "request: %r" % request)
    
            if isinstance(request, ScanRequest):
                # Drop this request if the database is already up-to-date.
                db = self.mgr.db
                buf = request.buf
                status = "changed"
                if not request.force:
                    scan_time_in_db = db.get_buf_scan_time(buf)
                    if scan_time_in_db is not None \
                       and scan_time_in_db > request.mtime:
                        log.debug("indexer: drop %s: have up-to-date data for "
                                  "%s in the db", request, buf)
                        status = "skipped"
                        return

                buf.scan(mtime=request.mtime)

            elif isinstance(request, XMLParseRequest):
                request.buf.xml_parse()

            # Currently these two are somewhat of a DB zone-specific hack.
            #TODO: The standard DB "lib" iface should grow a
            #      .preload() (and perhaps .can_preload()) with a
            #      ctlr arg. This should be unified with the current
            #      StdLib.preload().
            elif isinstance(request, PreloadBufLibsRequest):
                for lib in request.buf.libs:
                    if isinstance(lib, (LangDirsLib, MultiLangDirsLib)):
                        for dir in lib.dirs:
                            lib.ensure_dir_scanned(dir)
            elif isinstance(request, PreloadLibRequest):
                lib = request.lib
                assert isinstance(lib, (LangDirsLib, MultiLangDirsLib))
                for dir in lib.dirs:
                    lib.ensure_dir_scanned(dir)

        finally:
            if isinstance(request, ScanRequest):
                request.complete(status)
                if self.on_scan_complete:
                    try:
                        self.on_scan_complete(request)
                    except:
                        log.exception("ignoring exception in Indexer "
                                      "on_scan_complete callback")


#TODO: I believe this is unused. Drop it.
class BatchUpdater(threading.Thread):
    """A scheduler thread for batch updates to the CIDB.

    Usage:
    
        # May want to have a subclass of BatchUpdater for fine control.
        updater = BatchUpdater()
        updater.add_request(...)  # Make one or more requests.
        
        mgr.batch_update(updater=updater)  # This will start the updater.
        
        # Optionally use/override methods on the updater to control/monitor
        # the update.
        # Control methods:
        #   abort()                 Abort the update.
        #   join(timeout=None)      Wait for the update to complete.
        #
        # Query methods:
        #   num_files_to_process()
        #   is_aborted()
        #
        # Monitoring methods (need to override these in subclass to catch):
        #   debug(msg, *args)
        #   info(msg, *args)
        #   warn(msg, *args)
        #   error(msg, *args)
        #   progress(stage, obj)
        #   done(reason)            Called when complete.

    Dev Notes:
    - Yes, there are two ways to get code run on completion:
        .start(..., on_complete=None)   intended for the controlling Citadel
        .done()                         intended for the sub-classing user
    """
    citadel = None
    on_complete = None
    _aborted = None

    def __init__(self):
        XXX
        threading.Thread.__init__(self, name="CodeIntel Batch Scheduler")
        self.setDaemon(True)

        self._requests = Queue.Queue()
        self.mode = None # "upgrade", "non-upgrade" or None
        self._scheduler = None # lazily created (if necessary) Scheduler

        #XXX Need these two anymore?
        self._completion_reason = None
        self._had_errors = False

    def start(self, citadel, on_complete=None):
        self.citadel = citadel
        self.on_complete = on_complete
        threading.Thread.start(self)

    def abort(self):
        """Abort the batch update.
        
        XXX The scheduler.stop() call will *block* until the scheduler is
            done. Don't want that, but need to rationalize with other
            calls to Scheduler.stop().
        """
        self._aborted = True
        if self._scheduler:
            self._scheduler.stop()
    def is_aborted(self):
        return self._aborted

    def done(self, reason):
        """Called when the update is complete.
        
            "reason" is a short string indicating how the batch update
                completed. Currently expected values are (though this
                may not be rigorous):
                    aborted
                    error
                    success
                    failed      (from Scheduler)
                    completed   (from Scheduler)
                    stopped     (from Scheduler)
                XXX Might be helpful to rationalize these.
        """
        self.info("done: %s", reason)

    def add_request(self, type, path, language=None, extra=None):
        """Add a batch request
        
            "type" is one of:
                language    scan a language installation
                cix         import a CIX file
                directory   scan a source directory
                upgrade     upgrade a CIDB file to the current version
            "path", depending on "type" is the full path to:
                language    a language installation
                cix         a CIX file
                directory   a source directory
                upgrade     a CIDB file
            "language", depending on "type" is:
                language    the language of the language installation
                cix         (not relevant, should be None)
                directory   the language of the source directory
                upgrade     (not relevant, should be None)
            "extra" is an optional (null if not used) extra value depending
                on the type, path and/or language of the request that may be
                request for processing it. For example, a PHP language batch
                update request uses the "extra" field to specify the
                "php.ini"-config-file path.
        """
        if self.isAlive():
            raise CodeIntelError("cannot add a batch update request while "
                                 "the batch scheduler is alive")
        if type in ("language", "cix", "directory", "upgrade"):
            if type in ("language", "cix", "directory"):
                if self.mode == "upgrade":
                    raise CodeIntelError("cannot mix 'upgrade' batch requests "
                                         "with other types: (%s, %s, %s, %s)"
                                         % (type, path, language, extra))
                self.mode = "non-upgrade"
            elif type == "upgrade":
                if self.mode == "non-upgrade":
                    raise CodeIntelError("cannot mix 'upgrade' batch requests "
                                         "with other types: (%s, %s, %s, %s)"
                                         % (type, path, language, extra))
                self.mode = "upgrade"
            self._requests.put( (type, path, language, extra) )
        else:
            raise CodeIntelError("unknown batch update request type: '%s'"
                                 % type)

    def num_files_to_process(self):
        """Return the number of files remaining to process."""
        #XXX Might want to do something for "upgrade" mode here.
        if self._scheduler:
            return self._scheduler.getNumRequests()
        else:
            return 0

    def progress(self, msg, data):
        """Report progress.
        
            "msg" is some string, generally used to indicate a stage of
                processing
            "data" is some object dependent on the value of "msg".
        """
        self.info("progress: %s %r", msg, data)
    def debug(self, msg, *args):
        log.debug(msg, *args)
    def info(self, msg, *args):
        log.info(msg, *args)
    def warn(self, msg, *args):
        log.warn(msg, *args)
    def error(self, msg, *args):
        log.error(msg, *args)

    def _subscheduler_request_started(self, request):
        """Callback from sub-Scheduler thread."""
        self.progress("scanning", request)

    def _subscheduler_completed(self, reason):
        """Callback from sub-Scheduler thread."""
        self._completion_reason = reason

    def _get_scheduler(self):
        if not self._scheduler:
            self._scheduler = Scheduler(Scheduler.MODE_ONE_SHOT,
                                        self.citadel,
                                        None,
                                        self._subscheduler_request_started,
                                        self._subscheduler_completed)
        return self._scheduler

    def run(self):
        log.debug("batch scheduler thread: start")
        self.errors = []
        try:
            while 1:
                if self._aborted:
                    self._completion_reason = "aborted"
                    break

                try:
                    type_, path, lang, extra = self._requests.get_nowait()
                    self.debug("handle %r batch update request: "
                               "path=%r, language=%r, extra=%r",
                               type_, path, lang, extra)
                    if type_ == "upgrade":
                        self._handle_upgrade_request(path)
                    elif type_ == "language":
                        self._handle_lang_request(path, lang, extra)
                    elif type_ == "cix":
                        self._handle_cix_request(path)
                    elif type_ == "directory":
                        self._handle_directory_request(path, lang)
                    else:
                        raise CitadelError(
                            "unexpected batch request type: '%s'" % type_)
                except Queue.Empty:
                    break
                except Exception, ex:
                    self._had_errors = True
                    self.error("unexpected error handling batch update:\n%s",
                               _indent(traceback.format_exc()))
                    break

            if self._had_errors:
                log.debug("batch scheduler thread: error out")
                self._completion_reason = "error"
            elif self.mode == "upgrade":
                self._completion_reason = "success"
            elif self._scheduler: # No Scheduler for "upgrade" batch mode.
                # Phase 2: start the scheduler and wait for it to complete.
                self._scheduler.start()
                self._scheduler.join()
                if self._had_errors:
                    self._completion_reason = "error"
                else:
                    self._completion_reason = "success"
        finally:
            log.debug("batch scheduler thread: stop scheduler")
            if self._scheduler:
                self._scheduler.stop()
            log.debug("batch scheduler thread: scheduler stopped, call on_complete")
            if self.on_complete:
                try:
                    self.on_complete()
                except:
                    log.exception("error in batch scheduler on_complete "
                                  "(ignoring)")
            log.debug("batch scheduler thread: on_complete called, call done")
            self.done(self._completion_reason)
            log.debug("batch scheduler thread: done called")
        log.debug("batch scheduler thread: end")

    def _cidb_upgrade_progress_callback(self, stage, percent):
        self.progress("upgrade", (stage, percent))

    def _handle_upgrade_request(self, dbPath):
        db = Database(self.citadel)
        starttime = time.time()
        try:
            currVer = db.upgrade(dbPath, self._cidb_upgrade_progress_callback)
        except CodeIntelError, ex:
            self._had_errors = True
            self.error("Error upgrading CIDB: %s\n%s",
                       ex, _indent(traceback.format_exc()))
            return

        #XXX Re-evaluate this. Might make more sense in the Komodo-specific
        #    batch update controller now.
        # Komodo-specific HACK: Allow for a more pleasing user experience
        # by making sure the "Upgrading Database" dialog is up for at
        # least 2 seconds, rather than flashing for a quick upgrade.
        endtime = time.time()
        elapsed = endtime - starttime
        if elapsed < 2.0:
            time.sleep(2.0-elapsed)

    def _handle_cix_request(self, path):
        self.progress("importing", path)
        #XXX Consider not bothering if MD5 of file is already in DB.
        #       md5sum = md5(cix).hexdigest()
        #    c.f. "Can an MD5 for a CIX file be added?" in my notes.
        try:
            fin = open(path, 'r')
            try:
                cix = fin.read()
            finally:
                fin.close()
        except EnvironmentError, ex:
            self._had_errors = True
            self.error("Error importing CIX file '%s': %s\n%s",
                       path, ex, _indent(traceback.format_exc()))
            return
        db = Database(self.citadel)
        try:
            db.update(cix, recover=0, scan_imports=False)
        except CodeIntelError, ex:
            self._had_errors = True
            self.error("Error importing CIX file '%s': %s\n%s",
                       path, ex, _indent(traceback.format_exc()))
            return

    def _handle_lang_request(self, path, lang, extra):
        if lang == "*":
            langs = self.citadel.get_supported_langs()
        else:
            langs = [lang]

        for lang in langs:
            # See if have any pre-created CIX files for this language to use
            # instead of or in addition to actually scanning the core
            # library.
            stdcix = os.path.join(os.path.dirname(__file__),
                                  lang.lower()+".cix")
            if os.path.exists(stdcix):
                self._handle_cix_request(stdcix)

            try:
                importer = self.citadel.import_handler_from_lang(lang)
            except CodeIntelError, ex:
                if lang != "*":
                    self._had_errors = True
                    self.error("cannot handle 'language' batch update "
                               "request for %s: %s", lang, ex)
                continue
            try:
                importer.setCorePath(path, extra)
                UPDATE_EVERY = 50
                n = 0
                scheduler = self._get_scheduler()
                for file in importer.genScannableFiles(skipRareImports=True,
                                                       importableOnly=True):
                    if n % UPDATE_EVERY == 0:
                        self.progress("gathering files", n)
                        if self._aborted:
                            break
                    r = ScanRequest(file, lang, PRIORITY_IMMEDIATE,
                                    scan_imports=False)
                    scheduler.addRequest(r)
                    n += 1
            except CodeIntelError, ex:
                self._had_errors = True
                self.error("error handling %s request: %s\n%s",
                           lang, ex, _indent(traceback.format_exc()))

    def _handle_directory_request(self, path, lang):
        if lang == "*":
            langs = self.citadel.mgr.get_citadel_langs()
        else:
            langs = [lang]

        for lang in langs:
            try:
                importer = self.citadel.import_handler_from_lang(lang)
            except CodeIntelError, ex:
                if lang == "*":
                    continue
                else:
                    raise CodeIntelError("cannot handle 'directory' batch "
                                         "update request for '%s': %s"
                                         % (lang, ex))
            UPDATE_EVERY = 10
            n = 0
            scheduler = self._get_scheduler()
            for file in importer.genScannableFiles([path]):
                if n % UPDATE_EVERY == 0:
                    self.progress("gathering files", n)
                    if self._aborted:
                        break
                r = ScanRequest(file, lang, PRIORITY_IMMEDIATE,
                                scan_imports=False)
                scheduler.addRequest(r)
                n += 1



#---- internal support stuff

# Recipe: indent (0.2.1) in C:\trentm\tm\recipes\cookbook
def _indent(s, width=4, skip_first_line=False):
    """_indent(s, [width=4]) -> 's' indented by 'width' spaces

    The optional "skip_first_line" argument is a boolean (default False)
    indicating if the first line should NOT be indented.
    """
    lines = s.splitlines(1)
    indentstr = ' '*width
    if skip_first_line:
        return indentstr.join(lines)
    else:
        return indentstr + indentstr.join(lines)


