from trainingset import client, model

# Model training flows

# (1) Create a TrainingSetVersion and use it for training ---------------------

training_df = cleaning_feature_eng_etc()

tsv = client.create_training_set_version(
    training_set_name="my_training_set",
    df=training_df,
    key_columns=["user_id", "transaction_id"],
    target_columns="is_fraud",
    exclude_columns=["extra_column1", "extra_colum2"],
    meta={"experiment_id": "123456"},
    monitoring_meta={"categorical_columns": ["categorical_column1", "categorical_column2"]},
)

ts = client.get_training_set_version("my_training_set")

# optionally change permissions
ts.add_collaborator_names(["user2, user3"])

# Train a model
train_model(tsv.load_pandas())

# (2) Model training from an existing version ---------------------------------

tsv = client.get_training_set_version("my_training_set", number=tsv.number)

# all versions in a training set
for t in client.list_training_set_versions(filter={"training_set_name": "my_training_set"}):
    if t.id == desired_version:
        tsv = t
        break

# all versions is a project
for t in client.list_training_set_versions(filter={"project_name": "gmatev/quick-start"}):
    if t.training_set.name == "my_training_set" and t.number == desired_version:
        tsv = t
        break

tsv = client.list_training_set_versions(filter={"meta": {"experiment_id": "123456"}})[0]

train_model(tsv.load_pandas())

# (3) Change Training set permissions -----------------------------------------

ts = client.get_training_set(name="my_training_set")
ts.add_permission("new_user")

# persist the change
client.update_training_set(ts)

# Monitoring usage

# All training sets in a project

project_ts = client.list_training_set_versions(filter={"project_name": "gmatev/quick-start"})

# get monitoring specific meta-data
tsv = client.get_training_set_version("my_training_set", tsv.number)
print(tsv.monitoring_meta)

# get target variables
timestamp_columns = tsv.monitoring_meta.timestamp_columns
cardinal_cols = tsv.monitoring_meta.categorical_columns
ordinal_cols = tsv.monitoring_meta.ordinal_columns
target_cols = tsv.target_columns

# schema of raw data
tsv.load_raw_pandas().dtypes.to_json()
