from collections import defaultdict
class Request:
    def __init__(self,environ) -> None:
        self.queries= defaultdict()
        for key,val in environ.items():
            setattr(self,key.replace(".","_").lower(),val)

        if self.query_string:
            request_queries=self.query_string.split("&")

            for query in request_queries:
                query_key,query_value=query.split("=")

                self.queries[query_key]=query_value
