# requires falcon, gunicorn

import falcon
import json

import mongodb_api as mongo



ALLOWED_ORIGINS = 'http://localhost'

class CorsMiddleware(object):
	def process_request(self, req, resp):
		origin = req.get_header('Origin')
		#if origin is not None and origin in ALLOWED_ORIGINS:
		#	resp.set_header('Access-Control-Allow-Origin', origin)
		resp.set_header('Access-Control-Allow-Origin', '*')


class TopicsResource(object):
	def on_get(self, req, resp):
		resp.status = falcon.HTTP_200  
		resp.body = mongo.get_topics()

class AuthorTopicsResource(object):
	def on_get(self, req, resp):
		id = req.get_param("id")
		resp.status = falcon.HTTP_200  
		resp.body =  mongo.get_author_topics(id)

class GetMessageResource(object):
	def on_get(self, req, resp):
		id = req.get_param("id")
		resp.status = falcon.HTTP_200  
		resp.body =  mongo.get_message(id)

class GetMessageListResource(object):
	def on_get(self, req, resp):
		id = req.get_param("id");
		resp.status = falcon.HTTP_200  
		resp.body =  mongo.get_message_list(id)




# falcon.API instances are callable WSGI apps
app = application = falcon.API(middleware=[CorsMiddleware()])

topics_resource = TopicsResource()
author_topics_resource = AuthorTopicsResource()
get_message_resource = GetMessageResource()
get_message_list_resource = GetMessageListResource()

# Resources are represented by long-lived class instances
app.add_route('/topics', topics_resource)
app.add_route('/author_topics', author_topics_resource)
app.add_route('/get_message', get_message_resource)
app.add_route('/get_message_list', get_message_list_resource)

#app.add_route('/model', model_api)


# Run as
#gunicorn gunicorn_api -b :18000 --reload

