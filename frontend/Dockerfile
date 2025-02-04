FROM node:18-alpine
WORKDIR /frontend
ADD . .
RUN npm install -g serve
RUN npm install
RUN npm run build
CMD [ "/bin/sh", "-c", "npm run build && serve -s build" ]