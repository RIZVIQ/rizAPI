# def app(environ,start_response):
#     '''environ-> information about the request,
#        start_response-> response code,
#        returns the particulat text in bit format
#     '''
#     print(environ)
#     start_response("200",headers=[])
#     return [b"Hello Master!!"]

import inspect
import types
from response import Response
from parse import parse
from request import Request

SUPPORTED_REQUEST_METHODS={'GET','POST','DELETE'}
class RizApi:
    def __init__(self,middlewares=[]):
        self.routes={}
        self.middlewares=middlewares
        self.route_specific_middleware={}
        
    # ''' self.routes-> {
    #     '\users : {'GET':handler}
    #     }
    # '''
        
    def __call__(self, environ,start_response):
        '''environ-> information about the request,
       start_response-> response code,
       returns the particulat text in bit format'''
    
        # print(environ)
        # start_response("200",headers=[])
        # return [b"Hello, Master!!"]
        response=Response()
        request=Request(environ)
        for middlewares in self.middlewares:
            if isinstance(middlewares,types.FunctionType):
                middlewares(request)
            else:
                raise ValueError("The middlewares can only be of type function.")
        for path,handler_dict in self.routes.items():
            res=parse(path,request.path_info)

            print(res)
            for request_method,handler in handler_dict.items():
                if request.request_method==request_method and res:
                    route_midware_list=self.route_specific_middleware[path][request_method]
                    for midware in route_midware_list:
                        if isinstance(midware,types.FunctionType):
                            midware(request)
                        else:
                            raise ValueError("The middlewares can only be of type function.")
                    handler(request,response,**res.named)
                    return response.as_wsgi(start_response)
                    
        return response.as_wsgi(start_response)
    def route_structure(self,path,handler,method_name,middlewares):
         path_name=path or f"/{handler.__name__}"
                    
         if path_name not in self.routes:
            self.routes[path_name]={}
         self.routes[path_name][method_name]=handler
         if path_name not in self.route_specific_middleware:
             self.route_specific_middleware[path_name]={}
             
         self.route_specific_middleware[path_name][method_name]=middlewares

        
         return handler

    def get(self,path=None,middlewares=[]):
        def wrapper(handler):
            return self.route_structure(path,handler,"GET",middlewares)
        return wrapper
    def post(self,path=None,middlewares=[]):
        def wrapper(handler):
            return self.route_structure(path,handler,"POST",middlewares)
        return wrapper
    def delete(self,path=None,middlewares=[]):
        def wrapper(handler):
            return self.route_structure(path,handler,"DELETE",middlewares)
    
    def route(self,path=None,middlewares=[]):
        def wrapper(handler):
            if isinstance(handler,type):
                class_objects=inspect.getmembers(handler, lambda x: inspect.isfunction(x) and not (x.__name__.startswith("__") and x.__name__.endswith("__") ) and x.__name__.upper() in SUPPORTED_REQUEST_METHODS)
                print(class_objects)
                for func_name,func_handler in class_objects:
                    self.route_structure(path or f"/{handler.__name__}",func_handler,func_name.upper(),middlewares)
            else:
                raise ValueError("@route can only be used for classes")
        return wrapper


    
