# swagger_client.DataTransfersApi

All URIs are relative to */*

Method | HTTP request | Description
------------- | ------------- | -------------
[**data_transfers_id_callback_post**](DataTransfersApi.md#data_transfers_id_callback_post) | **POST** /data-transfers/{id}/callback | Callback for data transfer from filetask
[**data_transfers_id_get**](DataTransfersApi.md#data_transfers_id_get) | **GET** /data-transfers/{id} | Get data transfer by ID
[**data_transfers_post**](DataTransfersApi.md#data_transfers_post) | **POST** /data-transfers | Create new data transfer

# **data_transfers_id_callback_post**
> RemotefsDataTransfer data_transfers_id_callback_post(id)

Callback for data transfer from filetask

Callback for data transfer from filetask

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.DataTransfersApi()
id = 'id_example' # str | ID of data transfer targetted for callback from filetask

try:
    # Callback for data transfer from filetask
    api_response = api_instance.data_transfers_id_callback_post(id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DataTransfersApi->data_transfers_id_callback_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| ID of data transfer targetted for callback from filetask | 

### Return type

[**RemotefsDataTransfer**](RemotefsDataTransfer.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **data_transfers_id_get**
> RemotefsDataTransfer data_transfers_id_get(id)

Get data transfer by ID

Get data transfer by ID

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.DataTransfersApi()
id = 'id_example' # str | ID of data transfer to retrieve

try:
    # Get data transfer by ID
    api_response = api_instance.data_transfers_id_get(id)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DataTransfersApi->data_transfers_id_get: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **id** | **str**| ID of data transfer to retrieve | 

### Return type

[**RemotefsDataTransfer**](RemotefsDataTransfer.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **data_transfers_post**
> RemotefsDataTransfer data_transfers_post(body)

Create new data transfer

Create new data transfer

### Example
```python
from __future__ import print_function
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint

# create an instance of the API class
api_instance = swagger_client.DataTransfersApi()
body = swagger_client.ServerCreateDataTransfer() # ServerCreateDataTransfer | Data transfer to create

try:
    # Create new data transfer
    api_response = api_instance.data_transfers_post(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DataTransfersApi->data_transfers_post: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**ServerCreateDataTransfer**](ServerCreateDataTransfer.md)| Data transfer to create | 

### Return type

[**RemotefsDataTransfer**](RemotefsDataTransfer.md)

### Authorization

No authorization required

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

