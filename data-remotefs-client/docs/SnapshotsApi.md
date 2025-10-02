# swagger_client.SnapshotsApi

All URIs are relative to */*

Method | HTTP request | Description
------------- | ------------- | -------------
[**rpc_create_snapshot_from_run_post**](SnapshotsApi.md#rpc_create_snapshot_from_run_post) | **POST** /rpc/create-snapshot-from-run | Create new snapshot from a run
[**rpc_delete_snapshot_post**](SnapshotsApi.md#rpc_delete_snapshot_post) | **POST** /rpc/delete-snapshot | Delete snapshot by ID
[**rpc_restore_snapshot_post**](SnapshotsApi.md#rpc_restore_snapshot_post) | **POST** /rpc/restore-snapshot | Restore snapshot to active state
[**snapshots_get**](SnapshotsApi.md#snapshots_get) | **GET** /snapshots | List snapshots
[**snapshots_id_get**](SnapshotsApi.md#snapshots_id_get) | **GET** /snapshots/{id} | Get snapshot by ID
[**snapshots_id_put**](SnapshotsApi.md#snapshots_id_put) | **PUT** /snapshots/{id} | Update Snapshot by ID
[**snapshots_post**](SnapshotsApi.md#snapshots_post) | **POST** /snapshots | Create new snapshot

# **rpc_create_snapshot_from_run_post**
> RemotefsSnapshot rpc_create_snapshot_from_run_post(body)

Create new snapshot from a run

Create new snapshot from a volumes mounted in a run, must be called by super user

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.SnapshotsApi()
body = swagger_client.ServerCreateSnapshotFromRun() # ServerCreateSnapshotFromRun | Snapshot to create from run ID

try:
    # Create new snapshot from a run
    api_response = api_instance.rpc_create_snapshot_from_run_post(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling SnapshotsApi->rpc_create_snapshot_from_run_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerCreateSnapshotFromRun**](ServerCreateSnapshotFromRun.md)| Snapshot to create from run ID | 

### Return type

[**RemotefsSnapshot**](RemotefsSnapshot.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **rpc_delete_snapshot_post**
> rpc_delete_snapshot_post(body)

Delete snapshot by ID

Delete a snapshot by ID

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.SnapshotsApi()
body = swagger_client.ServerSnapshotIDRequest() # ServerSnapshotIDRequest | Snapshot ID to delete

try:
    # Delete snapshot by ID
    api_instance.rpc_delete_snapshot_post(body)
except ApiException as e:
    print("Exception when calling SnapshotsApi->rpc_delete_snapshot_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerSnapshotIDRequest**](ServerSnapshotIDRequest.md)| Snapshot ID to delete | 

### Return type

void (empty response body)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **rpc_restore_snapshot_post**
> RemotefsSnapshot rpc_restore_snapshot_post(body)

Restore snapshot to active state

Restore snapshot to active state

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.SnapshotsApi()
body = swagger_client.ServerSnapshotIDRequest() # ServerSnapshotIDRequest | Snapshot ID to restore to active state

try:
    # Restore snapshot to active state
    api_response = api_instance.rpc_restore_snapshot_post(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling SnapshotsApi->rpc_restore_snapshot_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerSnapshotIDRequest**](ServerSnapshotIDRequest.md)| Snapshot ID to restore to active state | 

### Return type

[**RemotefsSnapshot**](RemotefsSnapshot.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **snapshots_get**
> ServerPaginatedSnapshots snapshots_get(limit=limit, offset=offset, order=order, search=search, sort_by=sort_by, volume_id=volume_id, run_id=run_id)

List snapshots

List snapshots

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.SnapshotsApi()
limit = 56 # int | Limit (optional)
offset = 56 # int | Offset (optional)
order = 'order_example' # str | Order (optional)
search = 'search_example' # str | Search (optional)
sort_by = 'sort_by_example' # str | Sort by (optional)
volume_id = ['volume_id_example'] # list[str] | Volume ID (optional)
run_id = ['run_id_example'] # list[str] | Volume ID (optional)

try:
    # List snapshots
    api_response = api_instance.snapshots_get(limit=limit, offset=offset, order=order, search=search, sort_by=sort_by, volume_id=volume_id, run_id=run_id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling SnapshotsApi->snapshots_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **limit** | **int**| Limit | [optional] 
 **offset** | **int**| Offset | [optional] 
 **order** | **str**| Order | [optional] 
 **search** | **str**| Search | [optional] 
 **sort_by** | **str**| Sort by | [optional] 
 **volume_id** | [**list[str]**](str.md)| Volume ID | [optional] 
 **run_id** | [**list[str]**](str.md)| Volume ID | [optional] 

### Return type

[**ServerPaginatedSnapshots**](ServerPaginatedSnapshots.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **snapshots_id_get**
> RemotefsSnapshot snapshots_id_get(id)

Get snapshot by ID

Get snapshot by ID

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.SnapshotsApi()
id = 'id_example' # str | ID of snapshot to retrieve

try:
    # Get snapshot by ID
    api_response = api_instance.snapshots_id_get(id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling SnapshotsApi->snapshots_id_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| ID of snapshot to retrieve | 

### Return type

[**RemotefsSnapshot**](RemotefsSnapshot.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **snapshots_id_put**
> RemotefsSnapshot snapshots_id_put(body, id)

Update Snapshot by ID

Update Snapshot by ID

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.SnapshotsApi()
body = swagger_client.ServerUpdateSnapshot() # ServerUpdateSnapshot | Snapshot to update
id = 'id_example' # str | ID of Snapshot to update

try:
    # Update Snapshot by ID
    api_response = api_instance.snapshots_id_put(body, id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling SnapshotsApi->snapshots_id_put: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerUpdateSnapshot**](ServerUpdateSnapshot.md)| Snapshot to update | 
 **id** | **str**| ID of Snapshot to update | 

### Return type

[**RemotefsSnapshot**](RemotefsSnapshot.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **snapshots_post**
> RemotefsSnapshot snapshots_post(body)

Create new snapshot

Create new snapshot

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.SnapshotsApi()
body = swagger_client.ServerCreateSnapshot() # ServerCreateSnapshot | Snapshot to create

try:
    # Create new snapshot
    api_response = api_instance.snapshots_post(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling SnapshotsApi->snapshots_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerCreateSnapshot**](ServerCreateSnapshot.md)| Snapshot to create | 

### Return type

[**RemotefsSnapshot**](RemotefsSnapshot.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

