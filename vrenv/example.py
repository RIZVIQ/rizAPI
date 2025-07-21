from main import RizApi
rizapi=RizApi()

#functionality testing

@rizapi.post("/post")
def post_user(re,res):
    res.send(['posted','user'],200)
@rizapi.get("/new/{id}")
def get_user(req,res,id):
    res.send(['rizviq','hussain'])

@rizapi.route("/userss")
class First:
    def __init__(self)->None:
        pass
    def get(req,res):
        print(req.queries)
        res.send("rizAPI",200)
    def post(req,res):
        res.send("hello",500)
