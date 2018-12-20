pipeline {
  agent any
  stages {
    stage('run unit test') {
      steps {
        sh '/usr/bin/python3 -m pytest tests/test.py'
      }
    }
  }
}