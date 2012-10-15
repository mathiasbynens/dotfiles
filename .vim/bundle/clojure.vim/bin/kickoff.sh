#! /usr/bin/env bash

GRADLE_REV="0.8"
GRADLE_URL="http://dist.codehaus.org/gradle/gradle-${GRADLE_REV}-bin.zip"
GRADLE_ZIP="gradle.zip"
GRADLE_DIR="gradle-${GRADLE_REV}"

PLUGIN_REV="1.3.0"
PLUGIN_URL="http://clojars.org/repo/clojuresque/clojuresque/${PLUGIN_REV}/clojuresque-${PLUGIN_REV}.jar"
PLUGIN_JAR="clojuresque-${PLUGIN_REV}.jar"

CACHE_DIR="cache"
CACHE_GRADLE_ZIP="${CACHE_DIR}/${GRADLE_ZIP}"
CACHE_GRADLE_DIR="${CACHE_DIR}/${GRADLE_DIR}"

if [ ! -e "${CACHE_DIR}" ]; then
    mkdir "${CACHE_DIR}"
fi

if [ ! -e "${CACHE_GRADLE_ZIP}" ]; then
    wget ${GRADLE_URL} -O "${CACHE_GRADLE_ZIP}"
fi

if [ ! -e "${CACHE_GRADLE_DIR}" ]; then
    pushd .
    cd "${CACHE_DIR}"
    unzip "${GRADLE_ZIP}"
    popd
fi

if [ ! -e "${CACHE_PLUGIN_DIR}" ]; then
    wget ${PLUGIN_URL} -O "${CACHE_GRADLE_DIR}/lib/${PLUGIN_JAR}"
fi

echo "clojure=clojuresque.ClojurePlugin" >> "${CACHE_GRADLE_DIR}/plugin.properties"

echo "Don't forget to set GRADLE_HOME!"
echo "export GRADLE_HOME=\"${CACHE_GRADLE_DIR}\""
