# Source: https://github.com/juven/maven-bash-completion

function_exists()
{
	declare -F $1 > /dev/null
	return $?
}

function_exists _get_comp_words_by_ref ||
_get_comp_words_by_ref ()
{
    local exclude cur_ words_ cword_;
    if [ "$1" = "-n" ]; then
        exclude=$2;
        shift 2;
    fi;
    __git_reassemble_comp_words_by_ref "$exclude";
    cur_=${words_[cword_]};
    while [ $# -gt 0 ]; do
        case "$1" in
            cur)
                cur=$cur_
            ;;
            prev)
                prev=${words_[$cword_-1]}
            ;;
            words)
                words=("${words_[@]}")
            ;;
            cword)
                cword=$cword_
            ;;
        esac;
        shift;
    done
}

function_exists __ltrim_colon_completions ||
__ltrim_colon_completions()
{
	if [[ "$1" == *:* && "$COMP_WORDBREAKS" == *:* ]]; then
		# Remove colon-word prefix from COMPREPLY items
		local colon_word=${1%${1##*:}}
		local i=${#COMPREPLY[*]}
		while [[ $((--i)) -ge 0 ]]; do
			COMPREPLY[$i]=${COMPREPLY[$i]#"$colon_word"}
		done
	fi
}

function_exists __find_mvn_projects ||
__find_mvn_projects()
{
    find . -name 'pom.xml' -not -path '*/target/*' -prune | while read LINE ; do
        local withoutPom=${LINE%/pom.xml}
        local module=${withoutPom#./}
        if [[ -z ${module} ]]; then
            echo "."
        else
            echo ${module}
        fi
    done
}

function_exists _realpath ||
_realpath () 
{
    if [[ -f "$1" ]]
    then
        # file *must* exist
        if cd "$(echo "${1%/*}")" &>/dev/null
        then
	    # file *may* not be local
	    # exception is ./file.ext
	    # try 'cd .; cd -;' *works!*
 	    local tmppwd="$PWD"
	    cd - &>/dev/null
        else
	    # file *must* be local
	    local tmppwd="$PWD"
        fi
    else
        # file *cannot* exist
        return 1 # failure    
    fi

    # reassemble realpath
    echo "$tmppwd"/"${1##*/}"
    return 1 #success
}

function_exists __pom_hierarchy ||
__pom_hierarchy()
{
    local pom=`_realpath "pom.xml"`
    POM_HIERARCHY+=("$pom")
    while [ -n "$pom" ] && grep -q "<parent>" "$pom"; do
	    ## look for a new relativePath for parent pom.xml
        local parent_pom_relative=`grep -e "<relativePath>.*</relativePath>" "$pom" | sed 's/.*<relativePath>//' | sed 's/<\/relativePath>.*//g'`

    	## <parent> is present but not defined, assume ../pom.xml
    	if [ -z "$parent_pom_relative" ]; then
    	    parent_pom_relative="../pom.xml"
    	fi 

    	## if pom exists continue else break
    	parent_pom=`_realpath "${pom%/*}/$parent_pom_relative"`
        if [ -n "$parent_pom" ]; then 
            pom=$parent_pom
    	else 
    	    break
        fi
    	POM_HIERARCHY+=("$pom")
    done
}

_mvn()
{
    local cur prev
    COMPREPLY=()
    POM_HIERARCHY=()
    __pom_hierarchy
    _get_comp_words_by_ref -n : cur prev

    local opts="-am|-amd|-B|-C|-c|-cpu|-D|-e|-emp|-ep|-f|-fae|-ff|-fn|-gs|-h|-l|-N|-npr|-npu|-nsu|-o|-P|-pl|-q|-rf|-s|-T|-t|-U|-up|-V|-v|-X"
    local long_opts="--also-make|--also-make-dependents|--batch-mode|--strict-checksums|--lax-checksums|--check-plugin-updates|--define|--errors|--encrypt-master-password|--encrypt-password|--file|--fail-at-end|--fail-fast|--fail-never|--global-settings|--help|--log-file|--non-recursive|--no-plugin-registry|--no-plugin-updates|--no-snapshot-updates|--offline|--activate-profiles|--projects|--quiet|--resume-from|--settings|--threads|--toolchains|--update-snapshots|--update-plugins|--show-version|--version|--debug"

    local common_clean_lifecycle="pre-clean|clean|post-clean"
    local common_default_lifecycle="validate|initialize|generate-sources|process-sources|generate-resources|process-resources|compile|process-classes|generate-test-sources|process-test-sources|generate-test-resources|process-test-resources|test-compile|process-test-classes|test|prepare-package|package|pre-integration-test|integration-test|post-integration-test|verify|install|deploy"
    local common_site_lifecycle="pre-site|site|post-site|site-deploy"
    local common_lifecycle_phases="${common_clean_lifecycle}|${common_default_lifecycle}|${common_site_lifecycle}"

    local plugin_goals_appengine="appengine:backends_configure|appengine:backends_delete|appengine:backends_rollback|appengine:backends_start|appengine:backends_stop|appengine:backends_update|appengine:debug|appengine:devserver|appengine:devserver_start|appengine:devserver_stop|appengine:endpoints_get_client_lib|appengine:endpoints_get_discovery_doc|appengine:enhance|appengine:rollback|appengine:set_default_version|appengine:start_module_version|appengine:stop_module_version|appengine:update|appengine:update_cron|appengine:update_dos|appengine:update_indexes|appengine:update_queues|appengine:vacuum_indexes"
    local plugin_goals_android="android:apk|android:apklib|android:clean|android:deploy|android:deploy-dependencies|android:dex|android:emulator-start|android:emulator-stop|android:emulator-stop-all|android:generate-sources|android:help|android:instrument|android:manifest-update|android:pull|android:push|android:redeploy|android:run|android:undeploy|android:unpack|android:version-update|android:zipalign|android:devices"
    local plugin_goals_ant="ant:ant|ant:clean"
    local plugin_goals_antrun="antrun:run"
    local plugin_goals_archetype="archetype:generate|archetype:create-from-project|archetype:crawl"
    local plugin_goals_assembly="assembly:single|assembly:assembly"
    local plugin_goals_build_helper="build-helper:add-resource|build-helper:add-source|build-helper:add-test-resource|build-helper:add-test-source|build-helper:attach-artifact|build-helper:bsh-property|build-helper:cpu-count|build-helper:help|build-helper:local-ip|build-helper:maven-version|build-helper:parse-version|build-helper:regex-properties|build-helper:regex-property|build-helper:released-version|build-helper:remove-project-artifact|build-helper:reserve-network-port|build-helper:timestamp-property"
    local plugin_goals_buildnumber="buildnumber:create|buildnumber:create-timestamp|buildnumber:help|buildnumber:hgchangeset"
    local plugin_goals_cargo="cargo:start|cargo:run|cargo:stop|cargo:deploy|cargo:undeploy|cargo:help"
    local plugin_goals_checkstyle="checkstyle:checkstyle|checkstyle:check"
    local plugin_goals_cobertura="cobertura:cobertura"
    local plugin_goals_findbugs="findbugs:findbugs|findbugs:gui|findbugs:help"
    local plugin_goals_dependency="dependency:analyze|dependency:analyze-dep-mgt|dependency:analyze-duplicate|dependency:analyze-only|dependency:analyze-report|dependency:build-classpath|dependency:copy|dependency:copy-dependencies|dependency:get|dependency:go-offline|dependency:help|dependency:list|dependency:list-repositories|dependency:properties|dependency:purge-local-repository|dependency:resolve|dependency:resolve-plugins|dependency:sources|dependency:tree|dependency:unpack|dependency:unpack-dependencies"
    local plugin_goals_deploy="deploy:deploy-file"
    local plugin_goals_ear="ear:ear|ear:generate-application-xml"
    local plugin_goals_eclipse="eclipse:clean|eclipse:eclipse"
    local plugin_goals_ejb="ejb:ejb"
    local plugin_goals_enforcer="enforcer:enforce|enforcer:display-info"
    local plugin_goals_exec="exec:exec|exec:java"
    local plugin_goals_failsafe="failsafe:integration-test|failsafe:verify"
    local plugin_goals_flyway="flyway:migrate|flyway:clean|flyway:info|flyway:validate|flyway:baseline|flyway:repair"
    local plugin_goals_gpg="gpg:sign|gpg:sign-and-deploy-file"
    local plugin_goals_grails="grails:clean|grails:config-directories|grails:console|grails:create-controller|grails:create-domain-class|grails:create-integration-test|grails:create-pom|grails:create-script|grails:create-service|grails:create-tag-lib|grails:create-unit-test|grails:exec|grails:generate-all|grails:generate-controller|grails:generate-views|grails:help|grails:init|grails:init-plugin|grails:install-templates|grails:list-plugins|grails:maven-clean|grails:maven-compile|grails:maven-functional-test|grails:maven-grails-app-war|grails:maven-test|grails:maven-war|grails:package|grails:package-plugin|grails:run-app|grails:run-app-https|grails:run-war|grails:set-version|grails:test-app|grails:upgrade|grails:validate|grails:validate-plugin|grails:war"
    local plugin_goals_gwt="gwt:browser|gwt:clean|gwt:compile|gwt:compile-report|gwt:css|gwt:debug|gwt:eclipse|gwt:eclipseTest|gwt:generateAsync|gwt:help|gwt:i18n|gwt:mergewebxml|gwt:resources|gwt:run|gwt:run-codeserver|gwt:sdkInstall|gwt:source-jar|gwt:soyc|gwt:test"
    local plugin_goals_help="help:active-profiles|help:all-profiles|help:describe|help:effective-pom|help:effective-settings|help:evaluate|help:expressions|help:help|help:system"
    local plugin_goals_hibernate3="hibernate3:hbm2ddl|hibernate3:help"
    local plugin_goals_idea="idea:clean|idea:idea"
    local plugin_goals_install="install:install-file"
    local plugin_goals_jacoco="jacoco:check|jacoco:dump|jacoco:help|jacoco:instrument|jacoco:merge|jacoco:prepare-agent|jacoco:prepare-agent-integration|jacoco:report|jacoco:report-integration|jacoco:restore-instrumented-classes"
    local plugin_goals_javadoc="javadoc:javadoc|javadoc:jar|javadoc:aggregate"
    local plugin_goals_jboss="jboss:start|jboss:stop|jboss:deploy|jboss:undeploy|jboss:redeploy"
    local plugin_goals_jboss_as="jboss-as:add-resource|jboss-as:deploy|jboss-as:deploy-only|jboss-as:deploy-artifact|jboss-as:redeploy|jboss-as:redeploy-only|jboss-as:undeploy|jboss-as:undeploy-artifact|jboss-as:run|jboss-as:start|jboss-as:shutdown|jboss-as:execute-commands"
    local plugin_goals_jetty="jetty:run|jetty:run-exploded|jetty:run-forked"
    local plugin_goals_jxr="jxr:jxr"
    local plugin_goals_license="license:format|license:check"
    local plugin_goals_liquibase="liquibase:changelogSync|liquibase:changelogSyncSQL|liquibase:clearCheckSums|liquibase:dbDoc|liquibase:diff|liquibase:dropAll|liquibase:help|liquibase:migrate|liquibase:listLocks|liquibase:migrateSQL|liquibase:releaseLocks|liquibase:rollback|liquibase:rollbackSQL|liquibase:status|liquibase:tag|liquibase:update|liquibase:updateSQL|liquibase:updateTestingRollback"
    local plugin_goals_nexus_staging="nexus-staging:close|nexus-staging:deploy|nexus-staging:deploy-staged|nexus-staging:deploy-staged-repository|nexus-staging:drop|nexus-staging:help|nexus-staging:promote|nexus-staging:rc-close|nexus-staging:rc-drop|nexus-staging:rc-list|nexus-staging:rc-list-profiles|nexus-staging:rc-promote|nexus-staging:rc-release|nexus-staging:release"
    local plugin_goals_pmd="pmd:pmd|pmd:cpd|pmd:check|pmd:cpd-check"
    local plugin_goals_properties="properties:read-project-properties|properties:write-project-properties|properties:write-active-profile-properties|properties:set-system-properties"
    local plugin_goals_release="release:clean|release:prepare|release:rollback|release:perform|release:stage|release:branch|release:update-versions"
    local plugin_goals_repository="repository:bundle-create|repository:bundle-pack|repository:help"
    local plugin_goals_scala="scala:add-source|scala:cc|scala:cctest|scala:compile|scala:console|scala:doc|scala:doc-jar|scala:help|scala:run|scala:script|scala:testCompile"
    local plugin_goals_scm="scm:add|scm:checkin|scm:checkout|scm:update|scm:status"
    local plugin_goals_site="site:site|site:deploy|site:run|site:stage|site:stage-deploy"
    local plugin_goals_sonar="sonar:sonar|sonar:help"
    local plugin_goals_source="source:aggregate|source:jar|source:jar-no-fork"
    local plugin_goals_surefire="surefire:test"
    local plugin_goals_tomcat6="tomcat6:help|tomcat6:run|tomcat6:run-war|tomcat6:run-war-only|tomcat6:stop|tomcat6:deploy|tomcat6:undeploy"
    local plugin_goals_tomcat7="tomcat7:help|tomcat7:run|tomcat7:run-war|tomcat7:run-war-only|tomcat7:deploy"
    local plugin_goals_tomcat="tomcat:help|tomcat:start|tomcat:stop|tomcat:deploy|tomcat:undeploy"
    local plugin_goals_liberty="liberty:create-server|liberty:start-server|liberty:stop-server|liberty:run-server|liberty:deploy|liberty:undeploy|liberty:java-dump-server|liberty:dump-server|liberty:package-server"
    local plugin_goals_versions="versions:display-dependency-updates|versions:display-plugin-updates|versions:display-property-updates|versions:update-parent|versions:update-properties|versions:update-child-modules|versions:lock-snapshots|versions:unlock-snapshots|versions:resolve-ranges|versions:set|versions:use-releases|versions:use-next-releases|versions:use-latest-releases|versions:use-next-snapshots|versions:use-latest-snapshots|versions:use-next-versions|versions:use-latest-versions|versions:commit|versions:revert"
    local plugin_goals_vertx="vertx:init|vertx:runMod|vertx:pullInDeps|vertx:fatJar"
    local plugin_goals_war="war:war|war:exploded|war:inplace|war:manifest"
    local plugin_goals_spring_boot="spring-boot:run|spring-boot:repackage"
    local plugin_goals_jgitflow="jgitflow:feature-start|jgitflow:feature-finish|jgitflow:release-start|jgitflow:release-finish|jgitflow:hotfix-start|jgitflow:hotfix-finish|jgitflow:build-number"
    local plugin_goals_wildfly="wildfly:add-resource|wildfly:deploy|wildfly:deploy-only|wildfly:deploy-artifact|wildfly:redeploy|wildfly:redeploy-only|wildfly:undeploy|wildfly:undeploy-artifact|wildfly:run|wildfly:start|wildfly:shutdown|wildfly:execute-commands"

    ## some plugin (like jboss-as) has '-' which is not allowed in shell var name, to use '_' then replace
    local common_plugins=`compgen -v | grep "^plugin_goals_.*" | sed 's/plugin_goals_//g' | tr '_' '-' | tr '\n' '|'`

    local options="-Dmaven.test.skip=true|-DskipTests|-DskipITs|-Dtest|-Dit.test|-DfailIfNoTests|-Dmaven.surefire.debug|-DenableCiProfile|-Dpmd.skip=true|-Dcheckstyle.skip=true|-Dtycho.mode=maven|-Dmaven.javadoc.skip=true|-Dgwt.compiler.skip|-Dcobertura.skip=true|-Dfindbugs.skip=true||-DperformRelease=true|-Dgpg.skip=true|-DforkCount"

    local profile_settings=`[ -e ~/.m2/settings.xml ] && grep -e "<profile>" -A 1 ~/.m2/settings.xml | grep -e "<id>.*</id>" | sed 's/.*<id>//' | sed 's/<\/id>.*//g' | tr '\n' '|' `
    
    local profiles="${profile_settings}|"
    for item in ${POM_HIERARCHY[*]}
    do
        local profile_pom=`[ -e $item ] && grep -e "<profile>" -A 1 $item | grep -e "<id>.*</id>" | sed 's/.*<id>//' | sed 's/<\/id>.*//g' | tr '\n' '|' `
        local profiles="${profiles}|${profile_pom}"
    done

    local IFS=$'|\n'

    if [[ ${cur} == -D* ]] ; then
      COMPREPLY=( $(compgen -S ' ' -W "${options}" -- ${cur}) )

    elif [[ ${prev} == -P ]] ; then
      if [[ ${cur} == *,* ]] ; then
        COMPREPLY=( $(compgen -S ',' -W "${profiles}" -P "${cur%,*}," -- ${cur##*,}) )
      else
        COMPREPLY=( $(compgen -S ',' -W "${profiles}" -- ${cur}) )
      fi

    elif [[ ${cur} == --* ]] ; then
      COMPREPLY=( $(compgen -W "${long_opts}" -S ' ' -- ${cur}) )

    elif [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -S ' ' -- ${cur}) )

    elif [[ ${prev} == -pl ]] ; then
        if [[ ${cur} == *,* ]] ; then
            COMPREPLY=( $(compgen -W "$(__find_mvn_projects)" -S ',' -P "${cur%,*}," -- ${cur##*,}) )
        else
            COMPREPLY=( $(compgen -W "$(__find_mvn_projects)" -S ',' -- ${cur}) )
        fi

    elif [[ ${prev} == -rf || ${prev} == --resume-from ]] ; then
        COMPREPLY=( $(compgen -d -S ' ' -- ${cur}) )

    elif [[ ${cur} == *:* ]] ; then
        local plugin
        for plugin in $common_plugins; do
          if [[ ${cur} == ${plugin}:* ]]; then
            ## note that here is an 'unreplace', see the comment at common_plugins
            var_name="plugin_goals_${plugin//-/_}"
            COMPREPLY=( $(compgen -W "${!var_name}" -S ' ' -- ${cur}) )
          fi
        done

    else
        if echo "${common_lifecycle_phases}" | tr '|' '\n' | grep -q -e "^${cur}" ; then
          COMPREPLY=( $(compgen -S ' ' -W "${common_lifecycle_phases}" -- ${cur}) )
        elif echo "${common_plugins}" | tr '|' '\n' | grep -q -e "^${cur}"; then
          COMPREPLY=( $(compgen -S ':' -W "${common_plugins}" -- ${cur}) )
        fi
    fi

    __ltrim_colon_completions "$cur"
}

complete -o default -F _mvn -o nospace mvn
complete -o default -F _mvn -o nospace mvnDebug
