pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'code-quality-gate'
        DOCKER_TAG = "${BUILD_NUMBER}"
        QUALITY_THRESHOLD = '6.0'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                }
            }
        }

        stage('Run Unit Tests') {
            steps {
                script {
                    docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").inside {
                        sh 'pip install -r requirements-dev.txt'
                        sh 'pytest tests/ -v --junitxml=reports/junit.xml --cov=app --cov-report=xml:reports/coverage.xml'
                    }
                }
            }
            post {
                always {
                    junit 'reports/junit.xml'
                    publishHTML([
                        reportName: 'Coverage Report',
                        reportDir: 'reports',
                        reportFiles: 'coverage.xml'
                    ])
                }
            }
        }

        stage('Code Linting') {
            steps {
                script {
                    docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").inside {
                        sh 'flake8 app/ tests/ --max-line-length=120 --exclude=__pycache__'
                    }
                }
            }
        }

        stage('Code Quality Gate') {
            steps {
                script {
                    docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").withRun('-p 8000:8000') { container ->
                        sh '''
                            for i in $(seq 1 30); do
                                if curl -s http://localhost:8000/health | grep -q "healthy"; then
                                    break
                                fi
                                sleep 1
                            done
                        '''

                        sh """
                            REPORT=\$(curl -s -X POST http://localhost:8000/api/v1/analyze/file \
                                -F "file=@sample_files/clean_code.py" \
                                -F "threshold=${QUALITY_THRESHOLD}")

                            echo "Quality Report:"
                            echo "\${REPORT}" | python -m json.tool

                            PASSED=\$(echo "\${REPORT}" | python -c "import sys,json; print(json.load(sys.stdin)['passed'])")

                            if [ "\${PASSED}" = "False" ]; then
                                echo "QUALITY GATE FAILED - Score below threshold ${QUALITY_THRESHOLD}"
                                exit 1
                            fi

                            echo "QUALITY GATE PASSED"
                        """
                    }
                }
            }
        }

        stage('Push Image') {
            when {
                branch 'main'
            }
            steps {
                script {
                    docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").push()
                    docker.image("${DOCKER_IMAGE}:${DOCKER_TAG}").push('latest')
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
