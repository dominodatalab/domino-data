# swagger_client.VolumesApi

All URIs are relative to */*

Method | HTTP request | Description
------------- | ------------- | -------------
[**account_authz_permissions_volumeid_post**](VolumesApi.md#account_authz_permissions_volumeid_post) | **POST** /account/authz/permissions/volume/:id | Get if user has all provided volume permissions
[**rpc_attach_volume_to_project_post**](VolumesApi.md#rpc_attach_volume_to_project_post) | **POST** /rpc/attach-volume-to-project | Attach volume to project
[**rpc_check_is_over_limit_post**](VolumesApi.md#rpc_check_is_over_limit_post) | **POST** /rpc/check-is-over-limit | Check whether requesting user is over allowed volume limit
[**rpc_delete_volume_post**](VolumesApi.md#rpc_delete_volume_post) | **POST** /rpc/delete-volume | Delete volume by ID
[**rpc_detach_volume_from_project_post**](VolumesApi.md#rpc_detach_volume_from_project_post) | **POST** /rpc/detach-volume-from-project | Detach volume from project
[**rpc_get_volume_mounts_post**](VolumesApi.md#rpc_get_volume_mounts_post) | **POST** /rpc/get-volume-mounts | Get volume mounts by project ID
[**rpc_mark_volume_for_deletion_post**](VolumesApi.md#rpc_mark_volume_for_deletion_post) | **POST** /rpc/mark-volume-for-deletion | Mark volume for deletion
[**rpc_restore_volume_post**](VolumesApi.md#rpc_restore_volume_post) | **POST** /rpc/restore-volume | Restore volume to active state
[**staging_volume_get**](VolumesApi.md#staging_volume_get) | **GET** /staging-volume | Get domino staging volume name
[**volumes_get**](VolumesApi.md#volumes_get) | **GET** /volumes | List volumes
[**volumes_id_connection_snippets_get**](VolumesApi.md#volumes_id_connection_snippets_get) | **GET** /volumes/{id}/connection-snippets | Get the connection snippets for a given volume to access as a datasource
[**volumes_id_get**](VolumesApi.md#volumes_id_get) | **GET** /volumes/{id} | Get volume by ID
[**volumes_id_grants_get**](VolumesApi.md#volumes_id_grants_get) | **GET** /volumes/{id}/grants | Get grants by Volume ID
[**volumes_id_grants_put**](VolumesApi.md#volumes_id_grants_put) | **PUT** /volumes/{id}/grants | Update grants by Volume ID
[**volumes_id_patch**](VolumesApi.md#volumes_id_patch) | **PATCH** /volumes/{id} | Update Volume
[**volumes_post**](VolumesApi.md#volumes_post) | **POST** /volumes | Create new volume
[**volumes_unique_name_unique_name_get**](VolumesApi.md#volumes_unique_name_unique_name_get) | **GET** /volumes/unique-name/{uniqueName} | Get a volume by unique name

# **account_authz_permissions_volumeid_post**
> bool account_authz_permissions_volumeid_post(body, id)

Get if user has all provided volume permissions

Get if user has all provided volume permissions

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
body = swagger_client.ServerVolumePermissionsRequest() # ServerVolumePermissionsRequest | Volume permissions and user to check against
id = 'id_example' # str | ID of Volume to check permissions against

try:
    # Get if user has all provided volume permissions
    api_response = api_instance.account_authz_permissions_volumeid_post(body, id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->account_authz_permissions_volumeid_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerVolumePermissionsRequest**](ServerVolumePermissionsRequest.md)| Volume permissions and user to check against | 
 **id** | **str**| ID of Volume to check permissions against | 

### Return type

**bool**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **rpc_attach_volume_to_project_post**
> RemotefsVolume rpc_attach_volume_to_project_post(body)

Attach volume to project

Attach volume to project

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
body = swagger_client.ServerUpdateVolumeProject() # ServerUpdateVolumeProject | Project ID to attach to Volume ID

try:
    # Attach volume to project
    api_response = api_instance.rpc_attach_volume_to_project_post(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->rpc_attach_volume_to_project_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerUpdateVolumeProject**](ServerUpdateVolumeProject.md)| Project ID to attach to Volume ID | 

### Return type

[**RemotefsVolume**](RemotefsVolume.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **rpc_check_is_over_limit_post**
> bool rpc_check_is_over_limit_post()

Check whether requesting user is over allowed volume limit

Check whether requesting user is over allowed volume limit

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()

try:
    # Check whether requesting user is over allowed volume limit
    api_response = api_instance.rpc_check_is_over_limit_post()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->rpc_check_is_over_limit_post: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

**bool**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **rpc_delete_volume_post**
> rpc_delete_volume_post(body)

Delete volume by ID

Delete a volume by ID

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
body = swagger_client.ServerVolumeIDRequest() # ServerVolumeIDRequest | Volume ID to delete

try:
    # Delete volume by ID
    api_instance.rpc_delete_volume_post(body)
except ApiException as e:
    print("Exception when calling VolumesApi->rpc_delete_volume_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerVolumeIDRequest**](ServerVolumeIDRequest.md)| Volume ID to delete | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **rpc_detach_volume_from_project_post**
> RemotefsVolume rpc_detach_volume_from_project_post(body)

Detach volume from project

Detach volume from project

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
body = swagger_client.ServerUpdateVolumeProject() # ServerUpdateVolumeProject | Project ID to detach from Volume ID

try:
    # Detach volume from project
    api_response = api_instance.rpc_detach_volume_from_project_post(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->rpc_detach_volume_from_project_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerUpdateVolumeProject**](ServerUpdateVolumeProject.md)| Project ID to detach from Volume ID | 

### Return type

[**RemotefsVolume**](RemotefsVolume.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **rpc_get_volume_mounts_post**
> list[RemotefsVolumeMount] rpc_get_volume_mounts_post(body)

Get volume mounts by project ID

Get volume and snapshot mounts by project ID and optional data plane ID or volume ID

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
body = swagger_client.ServerListVolumeMountsRequest() # ServerListVolumeMountsRequest | Filters to apply to returned volume mounts

try:
    # Get volume mounts by project ID
    api_response = api_instance.rpc_get_volume_mounts_post(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->rpc_get_volume_mounts_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerListVolumeMountsRequest**](ServerListVolumeMountsRequest.md)| Filters to apply to returned volume mounts | 

### Return type

[**list[RemotefsVolumeMount]**](RemotefsVolumeMount.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **rpc_mark_volume_for_deletion_post**
> RemotefsVolume rpc_mark_volume_for_deletion_post(body)

Mark volume for deletion

Mark volume for deletion

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
body = swagger_client.ServerVolumeIDRequest() # ServerVolumeIDRequest | Volume ID to mark for deletion

try:
    # Mark volume for deletion
    api_response = api_instance.rpc_mark_volume_for_deletion_post(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->rpc_mark_volume_for_deletion_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerVolumeIDRequest**](ServerVolumeIDRequest.md)| Volume ID to mark for deletion | 

### Return type

[**RemotefsVolume**](RemotefsVolume.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **rpc_restore_volume_post**
> RemotefsVolume rpc_restore_volume_post(body)

Restore volume to active state

Restore volume to active state

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
body = swagger_client.ServerVolumeIDRequest() # ServerVolumeIDRequest | Volume ID to restore to active state

try:
    # Restore volume to active state
    api_response = api_instance.rpc_restore_volume_post(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->rpc_restore_volume_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerVolumeIDRequest**](ServerVolumeIDRequest.md)| Volume ID to restore to active state | 

### Return type

[**RemotefsVolume**](RemotefsVolume.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **staging_volume_get**
> str staging_volume_get()

Get domino staging volume name

Get domino staging volume name

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()

try:
    # Get domino staging volume name
    api_response = api_instance.staging_volume_get()
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->staging_volume_get: %s\n" % e)
```

### Parameters
This endpoint does not need any parameter.

### Return type

**str**

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **volumes_get**
> ServerPaginatedVolumes volumes_get(limit=limit, offset=offset, order=order, search=search, sort_by=sort_by, filter_strictly_by_volume_roles=filter_strictly_by_volume_roles, project_id=project_id, data_plane_id=data_plane_id, status=status)

List volumes

List volumes

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
limit = 56 # int | Limit (optional)
offset = 56 # int | Offset (optional)
order = 'order_example' # str | Order (optional)
search = 'search_example' # str | Search (optional)
sort_by = 'sort_by_example' # str | Sort by (optional)
filter_strictly_by_volume_roles = true # bool | Filter strictly by volume roles (optional)
project_id = ['project_id_example'] # list[str] | Project ID (optional)
data_plane_id = ['data_plane_id_example'] # list[str] | Data Plane ID (optional)
status = ['status_example'] # list[str] | Status (optional)

try:
    # List volumes
    api_response = api_instance.volumes_get(limit=limit, offset=offset, order=order, search=search, sort_by=sort_by, filter_strictly_by_volume_roles=filter_strictly_by_volume_roles, project_id=project_id, data_plane_id=data_plane_id, status=status)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->volumes_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**| Limit | [optional] 
 **offset** | **int**| Offset | [optional] 
 **order** | **str**| Order | [optional] 
 **search** | **str**| Search | [optional] 
 **sort_by** | **str**| Sort by | [optional] 
 **filter_strictly_by_volume_roles** | **bool**| Filter strictly by volume roles | [optional] 
 **project_id** | [**list[str]**](str.md)| Project ID | [optional] 
 **data_plane_id** | [**list[str]**](str.md)| Data Plane ID | [optional] 
 **status** | [**list[str]**](str.md)| Status | [optional] 

### Return type

[**ServerPaginatedVolumes**](ServerPaginatedVolumes.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **volumes_id_connection_snippets_get**
> list[RemotefsConnectionSnippet] volumes_id_connection_snippets_get(id)

Get the connection snippets for a given volume to access as a datasource

Get the connection snippets for a given volume to access as a datasource

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
id = 'id_example' # str | Volume ID

try:
    # Get the connection snippets for a given volume to access as a datasource
    api_response = api_instance.volumes_id_connection_snippets_get(id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->volumes_id_connection_snippets_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| Volume ID | 

### Return type

[**list[RemotefsConnectionSnippet]**](RemotefsConnectionSnippet.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **volumes_id_get**
> RemotefsVolume volumes_id_get(id)

Get volume by ID

Get volume by ID

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
id = 'id_example' # str | ID of volume to retrieve

try:
    # Get volume by ID
    api_response = api_instance.volumes_id_get(id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->volumes_id_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| ID of volume to retrieve | 

### Return type

[**RemotefsVolume**](RemotefsVolume.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **volumes_id_grants_get**
> list[RemotefsVolumeGrant] volumes_id_grants_get(id)

Get grants by Volume ID

Get grants by Volume ID

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
id = 'id_example' # str | ID of volume to retrieve grants from

try:
    # Get grants by Volume ID
    api_response = api_instance.volumes_id_grants_get(id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->volumes_id_grants_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| ID of volume to retrieve grants from | 

### Return type

[**list[RemotefsVolumeGrant]**](RemotefsVolumeGrant.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **volumes_id_grants_put**
> RemotefsVolumeGrant volumes_id_grants_put(body, id)

Update grants by Volume ID

Update grants by Volume ID

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
body = [swagger_client.RemotefsVolumeGrantDTO()] # list[RemotefsVolumeGrantDTO] | New grants to replace current volume grants
id = 'id_example' # str | ID of volume to update grants

try:
    # Update grants by Volume ID
    api_response = api_instance.volumes_id_grants_put(body, id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->volumes_id_grants_put: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**list[RemotefsVolumeGrantDTO]**](RemotefsVolumeGrantDTO.md)| New grants to replace current volume grants | 
 **id** | **str**| ID of volume to update grants | 

### Return type

[**RemotefsVolumeGrant**](RemotefsVolumeGrant.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **volumes_id_patch**
> RemotefsVolume volumes_id_patch(body, id)

Update Volume

Update Volume

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
body = swagger_client.ServerUpdateVolumeRequest() # ServerUpdateVolumeRequest | Name and description fields to update
id = 'id_example' # str | ID of volume to retrieve

try:
    # Update Volume
    api_response = api_instance.volumes_id_patch(body, id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->volumes_id_patch: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerUpdateVolumeRequest**](ServerUpdateVolumeRequest.md)| Name and description fields to update | 
 **id** | **str**| ID of volume to retrieve | 

### Return type

[**RemotefsVolume**](RemotefsVolume.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **volumes_post**
> RemotefsVolume volumes_post(body)

Create new volume

Create new volume

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
body = swagger_client.ServerCreateVolumeRequest() # ServerCreateVolumeRequest | Volume to create

try:
    # Create new volume
    api_response = api_instance.volumes_post(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->volumes_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerCreateVolumeRequest**](ServerCreateVolumeRequest.md)| Volume to create | 

### Return type

[**RemotefsVolume**](RemotefsVolume.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **volumes_unique_name_unique_name_get**
> RemotefsVolume volumes_unique_name_unique_name_get(unique_name)

Get a volume by unique name

Get a volume by unique name

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.VolumesApi()
unique_name = 'unique_name_example' # str | Unique name of volume to retrieve

try:
    # Get a volume by unique name
    api_response = api_instance.volumes_unique_name_unique_name_get(unique_name)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling VolumesApi->volumes_unique_name_unique_name_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **unique_name** | **str**| Unique name of volume to retrieve | 

### Return type

[**RemotefsVolume**](RemotefsVolume.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

