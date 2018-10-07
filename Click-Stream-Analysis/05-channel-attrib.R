library(ChannelAttribution)

df <- read.csv('Markov.csv')
head(df)
colnames(df) <- c("Channel", "Count")

df$Channel <- gsub('\\]','', df$Channel)
df$Channel <- gsub('\\[','', df$Channel)
head(df)

a <- markov_model(df, var_path = 'Channel', var_conv = 'Count', sep=",")
a$total_conversions <- a$total_conversions/sum(df$Count)
a

