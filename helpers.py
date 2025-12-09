import pandas as pd

def combine():
    og_df = pd.read_csv("data\information_checkpoint.csv")
    og_df = og_df.drop(columns=["Unnamed: 0"])

    df_one = pd.read_csv("data\information_checkpoint_2.csv")
    df_one = df_one.drop(columns=["Unnamed: 0"])
    
    df_two = pd.read_csv("data\information_checkpoint_top.csv").reset_index(drop=True)
    df_two = df_two.drop(columns=["Unnamed: 0"])

    df_all = pd.concat([og_df, df_one, df_two], ignore_index=True)
    df_all.to_csv("finished.csv", index=False)

def clean():
    df = pd.read_csv("finished.csv")
    df = df[
        df['date'].apply(lambda x: pd.to_datetime(x, errors='coerce')).notna()
        & df['ticker'].str.match(r'^[A-Z]{1,5}$')
        & df['amount'].str.match(r'^\$[\d,]+ - \$[\d,]+$')
        # & df['type'].isin(['Purchase', 'Sale (Full)', 'Sale (Partial)'])
    ]
    df.to_csv("cleaned.csv", index=False)
clean()