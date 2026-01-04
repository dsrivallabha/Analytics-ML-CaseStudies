library(ChannelAttribution)

df <- read.csv('MergedChains.csv')
head(df)

df$Channel <- gsub('\\]','', df$Channel)
df$Channel <- gsub('\\[','', df$Channel)
head(df)

a <- markov_model(df, var_path = 'Channel', var_conv = 'Count', var_null = "NonConversionCount", sep=",")
a$total_conversions <- a$total_conversions/sum(df$Count)
a

