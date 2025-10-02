# swagger_client.FilesystemsApi

All URIs are relative to */*

Method | HTTP request | Description
------------- | ------------- | -------------
[**filesystems_get**](FilesystemsApi.md#filesystems_get) | **GET** /filesystems | List filesystem
[**filesystems_id_delete**](FilesystemsApi.md#filesystems_id_delete) | **DELETE** /filesystems/{id} | Delete filesystem by ID
[**filesystems_id_get**](FilesystemsApi.md#filesystems_id_get) | **GET** /filesystems/{id} | Get filesystem by ID
[**filesystems_id_put**](FilesystemsApi.md#filesystems_id_put) | **PUT** /filesystems/{id} | Update filesystem
[**filesystems_post**](FilesystemsApi.md#filesystems_post) | **POST** /filesystems | Create new filesystem
[**root_pvcs_get**](FilesystemsApi.md#root_pvcs_get) | **GET** /root-pvcs | List available PVCs in the domino-compute namespace with the netapp-storage label

# **filesystems_get**
> ServerPaginatedFilesystems filesystems_get(limit=limit, offset=offset, order=order, search=search, sort_by=sort_by, data_plane_id=data_plane_id)

List filesystem

List filesystem

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.FilesystemsApi()
limit = 56 # int | Limit (optional)
offset = 56 # int | Offset (optional)
order = 'order_example' # str | Order (optional)
search = 'search_example' # str | Search (optional)
sort_by = 'sort_by_example' # str | Sort by (optional)
data_plane_id = ['data_plane_id_example'] # list[str] | Data Plane ID (optional)

try:
    # List filesystem
    api_response = api_instance.filesystems_get(limit=limit, offset=offset, order=order, search=search, sort_by=sort_by, data_plane_id=data_plane_id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling FilesystemsApi->filesystems_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**| Limit | [optional] 
 **offset** | **int**| Offset | [optional] 
 **order** | **str**| Order | [optional] 
 **search** | **str**| Search | [optional] 
 **sort_by** | **str**| Sort by | [optional] 
 **data_plane_id** | [**list[str]**](str.md)| Data Plane ID | [optional] 

### Return type

[**ServerPaginatedFilesystems**](ServerPaginatedFilesystems.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **filesystems_id_delete**
> filesystems_id_delete(id)

Delete filesystem by ID

Delete a filesystem by ID

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.FilesystemsApi()
id = 'id_example' # str | ID of filesystem to delete

try:
    # Delete filesystem by ID
    api_instance.filesystems_id_delete(id)
except ApiException as e:
    print("Exception when calling FilesystemsApi->filesystems_id_delete: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| ID of filesystem to delete | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **filesystems_id_get**
> RemotefsFilesystem filesystems_id_get(id, include_hostname=include_hostname)

Get filesystem by ID

Get filesystem by ID

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.FilesystemsApi()
id = 'id_example' # str | ID of filesystem to retrieve
include_hostname = true # bool | Whether to include the data plane host name in response (optional)

try:
    # Get filesystem by ID
    api_response = api_instance.filesystems_id_get(id, include_hostname=include_hostname)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling FilesystemsApi->filesystems_id_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| ID of filesystem to retrieve | 
 **include_hostname** | **bool**| Whether to include the data plane host name in response | [optional] 

### Return type

[**RemotefsFilesystem**](RemotefsFilesystem.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **filesystems_id_put**
> RemotefsFilesystem filesystems_id_put(body, id)

Update filesystem

Update a filesystem. Can be updated if there are volumes associated with the filesystem

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.FilesystemsApi()
body = swagger_client.ServerFilesystem() # ServerFilesystem | Filesystem to update
id = 'id_example' # str | ID of filesystem to update

try:
    # Update filesystem
    api_response = api_instance.filesystems_id_put(body, id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling FilesystemsApi->filesystems_id_put: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerFilesystem**](ServerFilesystem.md)| Filesystem to update | 
 **id** | **str**| ID of filesystem to update | 

### Return type

[**RemotefsFilesystem**](RemotefsFilesystem.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **filesystems_post**
> RemotefsFilesystem filesystems_post(body)

Create new filesystem

Create new filesystem

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.FilesystemsApi()
body = swagger_client.ServerFilesystem() # ServerFilesystem | Filesystem to create

try:
    # Create new filesystem
    api_response = api_instance.filesystems_post(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling FilesystemsApi->filesystems_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerFilesystem**](ServerFilesystem.md)| Filesystem to create | 

### Return type

[**RemotefsFilesystem**](RemotefsFilesystem.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **root_pvcs_get**
> list[str] root_pvcs_get(data_plane_id=data_plane_id)

List available PVCs in the domino-compute namespace with the netapp-storage label

List available PVCs in the domino-compute namespace with the netapp-storage label

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.FilesystemsApi()
data_plane_id = 'data_plane_id_example' # str | Data Plane ID (optional)

try:
    # List available PVCs in the domino-compute namespace with the netapp-storage label
    api_response = api_instance.root_pvcs_get(data_plane_id=data_plane_id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling FilesystemsApi->root_pvcs_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **data_plane_id** | **str**| Data Plane ID | [optional] 

### Return type

**list[str]**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

