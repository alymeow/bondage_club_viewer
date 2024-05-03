FROM ubuntu:jammy
RUN sed -i 's/[a-z]*.ubuntu.com/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list && apt update
RUN apt install -y python3-pip
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple flask flask-sqlalchemy pytz simplejson
WORKDIR /root
COPY viewer.py /root/
COPY templates /root/templates
VOLUME ["/root/instance"]
EXPOSE 5000
CMD ["/usr/bin/python3", "viewer.py"]
