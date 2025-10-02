# swagger_client.AuthzApi

All URIs are relative to */*

Method | HTTP request | Description
------------- | ------------- | -------------
[**account_authz_permissions_authorizedactions_post**](AuthzApi.md#account_authz_permissions_authorizedactions_post) | **POST** /account/authz/permissions/authorizedactions | Gets all permissions for requesting user

# **account_authz_permissions_authorizedactions_post**
> ServerPermissionResponse account_authz_permissions_authorizedactions_post(body)

Gets all permissions for requesting user

Gets all permissions for requesting user with optional volume ID or project ID in context field

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.AuthzApi()
body = swagger_client.ServerPermissionRequest() # ServerPermissionRequest | Permissions to check user against

try:
    # Gets all permissions for requesting user
    api_response = api_instance.account_authz_permissions_authorizedactions_post(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling AuthzApi->account_authz_permissions_authorizedactions_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerPermissionRequest**](ServerPermissionRequest.md)| Permissions to check user against | 

### Return type

[**ServerPermissionResponse**](ServerPermissionResponse.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

