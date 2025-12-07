## Patient Profile Construction

### Download
- The dataset will be provided through PhysioNet and requires a credentialed PhysioNet account (currently under review). 
- Unzip the dataset in the `./src/data/final_data` folder, which is the default path for the PatientSim experiment.


### Prerequisites
Our patient profile construction is based on three datasets: MIMIC-IV (v3.1), MIMIC-IV-Note (v2.2), and MIMIC-IV-ED (v2.2).
All these source datasets require a credentialed Physionet credentialing. To access the source datasets, you must fulfill all of the following requirements:
1. Be a [credentialed user](https://physionet.org/settings/credentialing/)
    - If you do not have a PhysioNet account, register for one [here](https://physionet.org/register/).
    - Follow these [instructions](https://physionet.org/credential-application/) for credentialing on PhysioNet.
    - Complete the "CITI Data or Specimens Only Research" [training course](https://physionet.org/about/citi-course/).
2. Sign the data use agreement (DUA) for each project
    - https://physionet.org/sign-dua/mimiciv/3.1/
    - https://physionet.org/sign-dua/mimic-iv-ed/2.2/
    - https://physionet.org/sign-dua/mimic-iv-note/2.2/



### Data Preprocessing
After obtaining access, preprocess the data using the following script (with your PhysioNet credentials):
```
cd src
bash data_preprocessing/build_dataset.sh
```

Update your API key before running:
```
export GOOGLE_APPLICATION_CREDENTIALS="YOUR_GOOGLE_APPLICATION_CREDENTIALS_PATH"
export GOOGLE_PROJECT_ID="YOUR_PROJECT_ID"
export GOOGLE_PROJECT_LOCATION="YOUR_PROJECT_LOCATION"
```
**Note**: While this script mirrors our internal preprocessing, results may vary due to fluctuations in the API. For consistent outcomes, we recommend using the preprocessed dataset, which will be made available on PhysioNet.

<br />
