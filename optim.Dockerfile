FROM ubuntu:xenial
MAINTAINER Nicolas Herbaut <nherbaut@labi.fr>

RUN apt-get -y update && apt-get install -y build-essential libgmp3-dev libreadline6 libreadline6-dev python3-pip graphviz pkg-config zlib1g-dev libncurses5-dev bison flex python3 python3-dev libblas-dev liblapack-dev libatlas-base-dev gfortran libz-dev

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
RUN pip3 install sklearn scipy numpy matplotlib pandas pymysql jinja2 sqlalchemy cycler==0.10.0 decorator==4.0.9 haversine==0.4.5  networkx==1.11   pygraphml==2.0  pyparsing==2.1.1  python-dateutil==2.5.3 pytz==2016.4  six==1.10.0

RUN apt-get install vim python3-tk -y

RUN apt-get install r-base r-base-dev -y
RUN apt-get install python3-mysqldb -y

RUN R -q -e "install.packages('xts', repos='http://cran.rstudio.com/')"
RUN R -q -e "install.packages('forecast', repos='http://cran.rstudio.com/')"
RUN R -q -e "install.packages('optparse', repos='http://cran.rstudio.com/')"
RUN R -q -e "install.packages('rPython', repos='http://cran.rstudio.com/')"

WORKDIR /opt/simuservice/
RUN mkdir -p /opt/girafe/results
COPY ./offline /opt/simuservice/offline

#RUN echo "#!/usr/bin/env bash \n /etc/init.d/mysql start && mysql -u root -proot -h localhost -e 'CREATE database IF NOT EXISTS paper4;' && /opt/simuservice/optim.py --dest_folder=/opt/girafe/results \"\$@\" "> /opt/simuservice/bootstrap.sh
RUN echo "#!/usr/bin/env bash \n /opt/simuservice/optim.py --dest_folder=/opt/girafe/results \"\$@\" "> /opt/simuservice/bootstrap.sh
#RUN echo "#!/usr/bin/env bash \n /opt/simuservice/optim.py --json --base64 --dest_folder=/opt/girafe/results \"\$@\" "> /opt/simuservice/bootstrap.sh
COPY ./optim.py /opt/simuservice
RUN chmod +x ./bootstrap.sh
VOLUME ["/opt/girafe/results"]
ENTRYPOINT [ "/opt/simuservice/bootstrap.sh" ]
