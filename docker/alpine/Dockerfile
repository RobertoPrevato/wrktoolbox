# Docker image for wrk and wrk2
#
FROM python:3.7-alpine
LABEL author="Roberto Prevato <roberto.prevato@gmail.com>"

RUN echo "===> Installing  tools..."  && \
    apk --no-cache add git build-base libressl-dev zlib-dev wrk && \
    echo "===> Installing wrk2" && \
    git clone https://github.com/RobertoPrevato/wrk2.git wrk2 && \
    cd wrk2 && \
    make && \
    mv wrk wrk2 && \
    cp wrk2 /usr/local/bin && \
    cd ..

WORKDIR /home
CMD ["/bin/sh"]
