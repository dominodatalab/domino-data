from trainingset import client, model

# UC1: User creates training FeatureSet ---------------------------------------

training_df = cleaning_feature_eng_etc()

# Create FS version
client.create_training_set_version(TrainingSetVersion(
    training_set="my-training-set",  # XXX should we restrict the set of characters that can be used?
    timestamp_column="ts",
    independent_vars=["foo"],
    target_vars=["bar"],
    continuous_vars=["baz"],
    categorical_vars=["asdf"],
    ordinal_vars=["xyz"],
    name="something",
    description="blah blah",
    metadata={},
))

# UC2: User selects training FeatureSet when enabling monitoring --------------


# this is somewhat problematic because the set returned could be very
# large, how would the UI deal with that?

# make a filtering api that addresses the needs of dmm

client.get_training_set_versions(project_id="project_id")

# or:
for ts in client.get_training_sets("project_id"):
    tsvs = client.get_training_set_versions(training_set_name=ts.name)

# UC3: User is made aware of prediction FeatureSet name and ID ----------------

ts = client.get_training_sets("project_id")


# UC4: User accesses prediction FeatureSet to get row identifier --------------

ts = client.get_training_set_versions(
    training_set_name="my-training-set",
    asc=0,
)[0]

df = client.get_training_set_version_df()

# UC5: DMM continuously logs predictions to a FeatureSet ----------------------

# not doing this.
