/*

library identifier: "pipeline-reporting@jenkins",
        retriever: modernSCM([$class: 'GitSCMSource',
                              remote: "https://github.com/joejstuart/pipeline-reporting.git",
                              traits: [[$class: 'jenkins.plugins.git.traits.BranchDiscoveryTrait'],
                                       [$class: 'RefSpecsSCMSourceTrait',
                                        templates: [[value: '+refs/heads/*:refs/remotes/@{remote}/*'],
                                                    [value: '+refs/pull/*:refs/remotes/origin/pr/*']]]]])
*/
// add comment
@NonCPS
def changeLogs() {
    echo "new changeset"
    def changeLogSets = currentBuild.changeSets
    echo changeLogSets.toString()
	for (int i = 0; i < changeLogSets.size(); i++) {
		def entries = changeLogSets[i].items
		for (int j = 0; j < entries.length; j++) {
			def entry = entries[j]
			echo "${entry.commitId} by ${entry.author} on ${new Date(entry.timestamp)}: ${entry.msg}"
			def files = new ArrayList(entry.affectedFiles)
			for (int k = 0; k < files.size(); k++) {
				def file = files[k]
				echo "  ${file.editType.name} ${file.path}"
			}
		}
	}
}

pipeline {

    agent {
        kubernetes {
            cloud 'openshift'
            label 'stage-trigger-pr'
            containerTemplate {
                name 'jnlp'
                args '${computer.jnlpmac} ${computer.name}'
                image '172.30.254.79:5000/kubevirt/jenkins-contra-slave:latest'
                ttyEnabled false
                command ''
            }
        }
    }

    stages {
        stage("Get Changelog") {
            steps {
                node('master') {
                    script {
                        changeLogs()
                    }
                }
            }
        }
    }
}
