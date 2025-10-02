# swagger_client.TasksApi

All URIs are relative to */*

Method | HTTP request | Description
------------- | ------------- | -------------
[**tasks_import_blobs_key_update_get**](TasksApi.md#tasks_import_blobs_key_update_get) | **GET** /tasks/import-blobs/{key}/update | Get import blobs task update

# **tasks_import_blobs_key_update_get**
> RemotefsFiletaskTask tasks_import_blobs_key_update_get(key)

Get import blobs task update

Get import blobs task update

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.TasksApi()
key = 'key_example' # str | Key of import blobs task

try:
    # Get import blobs task update
    api_response = api_instance.tasks_import_blobs_key_update_get(key)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling TasksApi->tasks_import_blobs_key_update_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **key** | **str**| Key of import blobs task | 

### Return type

[**RemotefsFiletaskTask**](RemotefsFiletaskTask.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

