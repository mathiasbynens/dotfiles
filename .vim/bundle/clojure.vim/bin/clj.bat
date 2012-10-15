@ECHO OFF

REM # Copyright (c) Stephen C. Gilardi. All rights reserved.  The use and
REM # distribution terms for this software are covered by the Eclipse Public
REM # License 1.0 (http://opensource.org/licenses/eclipse-1.0.php) which can be
REM # found in the file epl-v10.html at the root of this distribution.  By
REM # using this software in any fashion, you are agreeing to be bound by the
REM # terms of this license.  You must not remove this notice, or any other,
REM # from this software.
REM #
REM # scgilardi (gmail)
REM # Created 7 January 2009
REM #
REM # Modified by Justin Johnson <justin _ honesthacker com> to run on Windows
REM # and to include a check for .clojure file in the current directory.
REM #
REM # Environment variables:
REM #
REM # Optional:
REM #
REM #  CLOJURE_EXT  The path to a directory containing (either directly or as
REM #               symbolic links) jar files and/or directories whose paths
REM #               should be in Clojure's classpath. The value of the
REM #               CLASSPATH environment variable for Clojure will be a list
REM #               of these paths followed by the previous value of CLASSPATH
REM #               (if any).
REM #
REM #  CLOJURE_JAVA The command to launch a JVM instance for Clojure
REM #               default: java
REM #               example: /usr/local/bin/java6
REM #
REM #  CLOJURE_OPTS Java options for this JVM instance
REM #               default:
REM #               example:"-Xms32M -Xmx128M -server"
REM #
REM # Configuration files:
REM # 
REM # Optional:
REM #
REM #  .clojure     A file sitting in the directory where you invoke ng-server.
REM #               Each line contains a single path that should be added to the classpath.
REM #

SETLOCAL ENABLEDELAYEDEXPANSION

REM # Add all jar files from CLOJURE_EXT directory to classpath
IF DEFINED CLOJURE_EXT FOR %%E IN ("%CLOJURE_EXT%\*") DO SET CP=!CP!;%%~fE

IF NOT DEFINED CLOJURE_JAVA SET CLOJURE_JAVA=java

REM # If the current directory has a .clojure file in it, add each path
REM # in the file to the classpath.
IF EXIST .clojure FOR /F %%E IN (.clojure) DO SET CP=!CP!;%%~fE

%CLOJURE_JAVA% %CLOJURE_OPTS% -cp "%CP%" clojure.main %1 %2 %3 %4 %5 %6 %7 %8 %9
