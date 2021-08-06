import featureset

# UC1: User creates training FeatureSet ---------------------------------------

client = featureset.client()

# note: client automatically adds project_id, execution_id, etc to metadata
fs = client.create_featureset(
    name="RF_training_features",
    type=featureset.FeatureSetType.TRAINING,
)

training_df = cleaning_feature_eng_etc()

# Create FS version
fs.create_version(
    df=training_df,
    timestamp_column="ts",
    independent_vars=[],
    target_vars=[],
    continuous_vars=[],
    categorical_vars=[],
    ordinal_vars=[],
    name="my first version",  # note a num column is automatically created
    metadata={},
    annotations={}
)

# UC2: User selects training FeatureSet when enabling monitoring --------------


# this is somewhat problematic because the set returned could be very
# large, how would the UI deal with that?
def get_all_feature_sets_and_versions(
        project_id,
        fs_type=featureset.FeatureSetType.TRAINING
):

    # TODO: paginated API needs work
    featuresets = client.get_featuresets_for_project(
        project_id,
        fs_type,
        offset=0,
        limit=100
    )

    fs_versions_in_project = []
    for fs in feature_sets:
        # TODO: paginated API needs work
        versions = featuresets.get_versions_for_project(
            project_id,
            offset=0,
            limit=100
        )
        fs_versions_in_project.append(versions)

   return fs_versions_in_project

# UC3: User is made aware of prediction FeatureSet name and ID ----------------

def get_feature_sets(project_id, fs_type=featureset.FeatureSetType.PREDICTION):
   return client.get_featuresets_for_project(project_id, fs_type, offset=0, limit=100)


# UC4: User accesses prediction FeatureSet to get row identifier --------------

client = featureset.client()
fs = client.get_featureset_by_name("modelID_predictions")

# note: current prototype includes get_latest_version(),
# get_versions_for_project(), do we have a sense of ways the user might
# want to select versions, or is it good enough to let the user filter on
# their end?
fsvs = fs.get_versions(offset=0, limit=100)
fs = fsvs[20]  # user selects version of interest

target_timeframe_df = fs.get_df()

# code to analyze the prediction dataframe, read row identifiers, and
# construct ground truth data

# UC5: DMM continuously logs predictions to a FeatureSet ----------------------

fs = client.get_featureset_by_name("my_first_featureset")

# DMM will buffer predictions and append to an existing FeatureSet in batches

fsv = fs.open_version(
    timestamp_column="ts",
    independent_vars = [],
    target_vars = [],
    continuous_vars = [],
    categorical_vars = [],
    ordinal_vars = [],
)

while (collecting_data):
    fsv.append(batched_predictions_df)

# At some point in the future
fsv.close()
