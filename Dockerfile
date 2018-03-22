FROM centos:latest

# To handle buildable attachments and compile cchardet
RUN yum -y update && yum -y --enablerepo=extras install epel-release && yum install -y zip unzip g++ libc-dev supervisor python36 wget && yum clean all
RUN wget https://bootstrap.pypa.io/get-pip.py && python3.6 get-pip.py


# Do like debian "onbuild" versions
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app
COPY requirements.txt /usr/src/app/
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . /usr/src/app

# prepare django
RUN python36 manage.py makemigrations
RUN python36 manage.py collectstatic --noinput
RUN mkdir /etc/supervisor.d && cp docker/django.ini /etc/supervisor.d/

# start django
EXPOSE 8000
CMD python36 manage.py migrate && supervisord -n
