FROM ubuntu:xenial
MAINTAINER Nicolas Herbaut <nherbaut@labi.fr> 

RUN apt-get -y update && apt-get install -y build-essential libgmp3-dev libreadline6 libreadline6-dev python-pip graphviz pkg-config python zlib1g-dev libncurses5-dev bison flex python2.7 python2.7-dev libblas-dev liblapack-dev libatlas-base-dev gfortran libz-dev

RUN mkdir /home/scip
COPY ./resources/scipoptsuite-3.2.1.tgz /home/scip

RUN cd /home/scip && tar  -zxvf scipoptsuite-3.2.1.tgz
WORKDIR /home/scip/scipoptsuite-3.2.1
RUN make
RUN make install INSTALLDIR=/usr/local
ENV PATH /home/scip/scipoptsuite-3.2.1/scip-3.2.1/bin/:$PATH




RUN echo "mysql-server mysql-server/root_password password root" | debconf-set-selections
RUN echo "mysql-server mysql-server/root_password_again password root" | debconf-set-selections

RUN apt-get -y install mysql-server
RUN pip install sklearn scipy numpy matplotlib pandas pymysql jinja2 sqlalchemy cycler==0.10.0 decorator==4.0.9 haversine==0.4.5  networkx==1.11   pygraphml==2.0  pyparsing==2.1.1  python-dateutil==2.5.3 pytz==2016.4  six==1.10.0
WORKDIR /opt/simuservice/
COPY ./offline /opt/simuservice/offline


CMD mysqld
