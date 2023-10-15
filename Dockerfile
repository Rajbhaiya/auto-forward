FROM python:latest 

ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY . .
RUN pip install -U pip wheel && \
    pip install -r requirements.txt
CMD ["bash", "start"]
