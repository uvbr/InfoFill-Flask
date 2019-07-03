from flask_restful import Api

from app import app
from .infofill import UserView,RoleView, ActivateAccount, Authenticate, AttachUserRole
from flask_restful.utils import cors

app.secret_key = 'nexii'

restServerInstance = Api(app)
restServerInstance.decorators=[cors.crossdomain(origin='*')]

restServerInstance.add_resource(AttachUserRole,"/api/v1.0/attach/user/role/",endpoint="AttachUserRole")
restServerInstance.add_resource(UserView,"/api/v1.0/user/",endpoint="UserView")
restServerInstance.add_resource(RoleView,"/api/v1.0/role/", endpoint="RoleView")
restServerInstance.add_resource(ActivateAccount,"/api/v1.0/activate/",endpoint="activate_account")
restServerInstance.add_resource(Authenticate,"/api/v1.0/auth/signin/",endpoint="Authenticate")

