library(CreditMetrics)

N <- 4
n <- 24*60*90
firmnames <- c("Current", "Power", "Vibration", "Temperature")

# correlation matrix
rho <- matrix(c(  1.0, 0.9, 0.8, 0.01,
                  0.9, 1.0, 0.7, 0.01,
                  0.8, 0.7, 1.0, 0.01,
                  0.01, 0.01, 0.01, 1.0), 4, 4, dimnames = list(firmnames, firmnames),
              byrow = TRUE)

z <- cm.rnorm.cor(N, n, rho)
a <- t(z)

b <- colnames(a)
write.table(a,file="test.csv", sep=',') # keeps the rownames

