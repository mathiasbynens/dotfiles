// monitors
var monLap = "1440x900";
var monExt = "1920x1080";

// generic operations
var opFullScreen = S.op("move", {
    "x" : "screenOriginX",
    "y" : "screenOriginY",
    "width" : "screenSizeX",
    "height" : "screenSizeY"
});

var opHalfScreenLeft = S.op("move", {
    "x" : "screenOriginX",
    "y" : "screenOriginY",
    "width" : "screenSizeX/2",
    "height" : "screenSizeY"
});

var opHalfScreenRight = S.op("move", {
    "x" : "screenOriginX+screenSizeX/2",
    "y" : "screenOriginY",
    "width" : "screenSizeX/2",
    "height" : "screenSizeY"
});

var opPushFullScreen = S.op("corner", {
    "direction": "top-left",
    "width": "screenSizeX",
    "height": "screenSizeY"
});

var opPushHalfScreen = S.op("push", {
    "direction": "left",
    "style": "bar-resize:screenSizeX/2"
});
var opPushHalfScreenLeft  = opPushHalfScreen;
var opPushHalfScreenRight = opPushHalfScreen.dup({ "direction": "right" });

var opLapFullScreen = opFullScreen.dup({ "screen": monLap });
var opLapHalfScreenLeft = opHalfScreenLeft.dup({ "screen": monLap });
var opLapHalfScreenRight = opHalfScreenRight.dup({ "screen": monLap });

var opExtFullScreen = opFullScreen.dup({ "screen": monExt });
var opExtHalfScreenLeft = opHalfScreenLeft.dup({ "screen": monExt });
var opExtHalfScreenRight = opHalfScreenRight.dup({ "screen": monExt });

// hashes
var hashLapGeneric = {
    "operations": [opLapFullScreen],
    "ignore-fail": true,
    "repeat": true
};

var hashExtGeneric = {
    "operations": [opExtFullScreen],
    "ignore-fail": true,
    "repeat": true
};

var hashSublimeText = hashExtGeneric;
var hashITerm = hashExtGeneric;
var hashGoogleChrome = hashLapGeneric;

// layouts
var layOne = S.lay("one monitor", {
    "iTerm": hashLapGeneric,
    "Google Chrome": hashLapGeneric,
    "Sublime Text": hashLapGeneric,
    "Spotify": hashLapGeneric
});

var layTwo = S.lay("two monitors", {
    "Sublime Text": hashExtGeneric,
    "iTerm": hashExtGeneric,
    "Google Chrome": hashGoogleChrome,
    "Spotify": hashExtGeneric
});

// defaults
S.def(1, layOne);
S.def(2, layTwo);

// bindings
S.bnda({
    "up:ctrl": opPushFullScreen,
    "left:ctrl": opPushHalfScreenLeft,
    "right:ctrl": opPushHalfScreenRight
});
