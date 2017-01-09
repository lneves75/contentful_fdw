FROM alpine:3.5

ENV LANG en_US.utf8

# Install postgres, bash (required by multicorn) and su-exec (required by docker-entrypoint)
RUN apk add --no-cache --update bash su-exec postgresql postgresql-dev

RUN mkdir /docker-entrypoint-initdb.d
RUN mkdir -p /var/run/postgresql && chown -R postgres /var/run/postgresql
ENV PGDATA /var/lib/postgresql/data
VOLUME /var/lib/postgresql/data

COPY docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]

# Install python for pgxnclient and multicorn
RUN apk add --no-cache --update python python-dev py-setuptools git build-base \
  # Install and upgrade Pip
  # make some useful symlinks that are expected to exist
  && if [[ ! -e /usr/bin/python ]];        then ln -sf /usr/bin/python2.7 /usr/bin/python; fi \
  && if [[ ! -e /usr/bin/python-config ]]; then ln -sf /usr/bin/python2.7-config /usr/bin/python-config; fi \
  && if [[ ! -e /usr/bin/idle ]];          then ln -sf /usr/bin/idle2.7 /usr/bin/idle; fi \
  && if [[ ! -e /usr/bin/pydoc ]];         then ln -sf /usr/bin/pydoc2.7 /usr/bin/pydoc; fi \
  && if [[ ! -e /usr/bin/easy_install ]];  then ln -sf /usr/bin/easy_install-2.7 /usr/bin/easy_install; fi \
  && easy_install pip \
  && pip install --upgrade pip

RUN pip install pgxnclient
RUN pgxn install multicorn

COPY requirements.txt /app/

RUN pip install -r /app/requirements.txt

WORKDIR /app

COPY . /app

RUN python setup.py install

EXPOSE 5432
CMD ["postgres"]
