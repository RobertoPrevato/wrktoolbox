# Docker image for wrk and wrk2
#
FROM  python:3.7
LABEL author="Roberto Prevato <roberto.prevato@gmail.com>"

RUN echo "===> Installing  tools..."  && \
    apt-get -y update && \
    apt-get -y install build-essential libssl-dev git zlib1g-dev && \
    \
    echo "===> Installing wrk" && \
    git clone https://github.com/RobertoPrevato/wrk.git wrk && \
    cd wrk && \
    make && \
    cp wrk /usr/local/bin && \
    cd .. && \
    \
    echo "===> Installing wrk2" && \
    git clone https://github.com/RobertoPrevato/wrk2.git wrk2 && \
    cd wrk2 && \
    make && \
    mv wrk wrk2 && \
    cp wrk2 /usr/local/bin && \
    cd .. && \
    \
    echo "===> Cleaning the system" && \
    apt-get -f -y --auto-remove remove build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /opt/wrk/

WORKDIR /home
CMD ["/bin/bash"]