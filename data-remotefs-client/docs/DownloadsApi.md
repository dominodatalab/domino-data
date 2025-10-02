# swagger_client.DownloadsApi

All URIs are relative to */*

Method | HTTP request | Description
------------- | ------------- | -------------
[**downloads_id_get**](DownloadsApi.md#downloads_id_get) | **GET** /downloads/{id} | Get download task status
[**downloads_post**](DownloadsApi.md#downloads_post) | **POST** /downloads | Create download archive

# **downloads_id_get**
> RemotefsFiletaskTask downloads_id_get(id, volume_id)

Get download task status

Get download task status

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.DownloadsApi()
id = 'id_example' # str | ID of downloads task
volume_id = 'volume_id_example' # str | ID of volume download task originates from

try:
    # Get download task status
    api_response = api_instance.downloads_id_get(id, volume_id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DownloadsApi->downloads_id_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| ID of downloads task | 
 **volume_id** | **str**| ID of volume download task originates from | 

### Return type

[**RemotefsFiletaskTask**](RemotefsFiletaskTask.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **downloads_post**
> RemotefsFiletaskTask downloads_post(body)

Create download archive

Create download archive

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.DownloadsApi()
body = swagger_client.ServerCreateDownloadArchiveRequest() # ServerCreateDownloadArchiveRequest | Create download request

try:
    # Create download archive
    api_response = api_instance.downloads_post(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DownloadsApi->downloads_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerCreateDownloadArchiveRequest**](ServerCreateDownloadArchiveRequest.md)| Create download request | 

### Return type

[**RemotefsFiletaskTask**](RemotefsFiletaskTask.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

