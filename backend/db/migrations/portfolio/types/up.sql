CREATE TYPE [BotPortfolio].[accounts] AS TABLE(
    [id] VARCHAR(36),
    [userId] INT NOT NULL,
    [name] NVARCHAR(50),
    [accountType] VARCHAR(20),
    [identificationCode] VARCHAR(20),
    [custodyCode] VARCHAR(20),
    [password] VARCHAR(255),
    [brokerName] VARCHAR(20),
    [brokerInvestorId] VARCHAR(20),
    [brokerAccountId] VARCHAR(20),
    [__createdAt__] VARCHAR(19),
    [__updatedAt__] VARCHAR(19)
);
GO

CREATE TYPE [BotPortfolio].[balances] AS TABLE(
    [id] VARCHAR(36),
    [brokerAccountId] VARCHAR(20) NOT NULL,
    [totalCash] BIGINT,
    [availableCash] BIGINT,
    [termDeposit] BIGINT,
    [depositInterest] BIGINT,
    [stockValue] BIGINT,
    [marginableAmount] BIGINT,
    [nonMarginableAmount] BIGINT,
    [totalDebt] BIGINT,
    [netAssetValue] BIGINT,
    [receivingAmount] BIGINT,
    [secureAmount] BIGINT,
    [depositFeeAmount] BIGINT,
    [maxLoanLimit] BIGINT,
    [withdrawableCash] BIGINT,
    [collateralValue] BIGINT,
    [orderSecured] BIGINT,
    [purchasingPower] BIGINT,
    [cashDividendReceiving] BIGINT,
    [marginDebt] FLOAT,
    [marginRate] FLOAT,
    [ppWithdraw] BIGINT,
    [blockMoney] BIGINT,
    [totalRemainDebt] FLOAT,
    [totalUnrealizedDebt] FLOAT,
    [blockedAmount] FLOAT,
    [advancedAmount] BIGINT,
    [advanceWithdrawnAmount] FLOAT,
    [__createdAt__] VARCHAR(19),
    [__updatedAt__] VARCHAR(19)
);
GO

CREATE TYPE [BotPortfolio].[orders] AS TABLE(
    [id] VARCHAR(36),
    [accountId] VARCHAR(36) NOT NULL,
    [brokerAccountId] VARCHAR(20),
    [side] VARCHAR(10) NOT NULL,
    [symbol] VARCHAR(10) NOT NULL,
    [price] INT NOT NULL,
    [quantity] INT NOT NULL,
    [orderType] VARCHAR(10) NOT NULL,
    [orderStatus] VARCHAR(10) NOT NULL,
    [fillQuantity] INT,
    [lastQuantity] INT,
    [lastPrice] INT,
    [averagePrice] INT,
    [transDate] VARCHAR(30),
    [createdDate] VARCHAR(30),
    [modifiedDate] VARCHAR(30),
    [leaveQuantity] INT,
    [canceledQuantity] INT,
    [priceSecure] INT,
    [error] VARCHAR(255),
    [__createdAt__] VARCHAR(19),
    [__updatedAt__] VARCHAR(19)
);
GO

CREATE TYPE [BotPortfolio].[deals] AS TABLE(
    [id] VARCHAR(36),
    [brokerAccountId] VARCHAR(20),
    [dealId] VARCHAR(10) NOT NULL,
    [symbol] VARCHAR(10) NOT NULL,
    [status] VARCHAR(10),
    [side] VARCHAR(10),
    [secure] FLOAT,
    [accumulateQuantity] INT NOT NULL,
    [tradeQuantity] INT NOT NULL,
    [closedQuantity] INT NOT NULL,
    [t0ReceivingQuantity] INT,
    [t1ReceivingQuantity] INT,
    [t2ReceivingQuantity] INT,
    [costPrice] FLOAT NOT NULL,
    [averageCostPrice] FLOAT NOT NULL,
    [marketPrice] FLOAT NOT NULL,
    [realizedProfit] FLOAT NOT NULL,
    [unrealizedProfit] FLOAT,
    [breakEvenPrice] FLOAT,
    [dividendReceivingQuantity] INT,
    [dividendQuantity] INT,
    [cashReceiving] FLOAT,
    [rightReceivingCash] INT,
    [t0ReceivingCash] FLOAT,
    [t1ReceivingCash] FLOAT,
    [t2ReceivingCash] FLOAT,
    [createdDate] VARCHAR(30),
    [modifiedDate] VARCHAR(30),
    [__createdAt__] VARCHAR(19),
    [__updatedAt__] VARCHAR(19)
);
GO

CREATE TYPE [BotPortfolio].[optimizedWeights] AS TABLE(
    [id] INT,
    [date] VARCHAR(10) NOT NULL,
    [symbol] VARCHAR(10) NOT NULL,
    [marketPrice] FLOAT NOT NULL,
    [initialWeight] DECIMAL(8,6) NOT NULL,
    [neutralizedWeight] DECIMAL(8,6),
    [limitedWeight] DECIMAL(8,6),
    [neutralizedLimitedWeight] DECIMAL(8,6),
    [algorithm] VARCHAR(50),

    [__createdAt__] VARCHAR(19),
    [__updatedAt__] VARCHAR(19)
);
GO

CREATE TYPE [BotPortfolio].[UniverseTopMonthly] AS TABLE(
    [id] INT,
    [year] INT NOT NULL,
    [month] INT NOT NULL,
    [symbol] VARCHAR(10) NOT NULL,
    [exchangeCode] VARCHAR(10) NOT NULL,
    [sectorL2] VARCHAR(50),
    [cap] FLOAT,
    [averageLiquidity21] FLOAT,
    [averageLiquidity63] FLOAT,
    [averageLiquidity252] FLOAT,
    [grossProfitQoQ] FLOAT,
    [roe] FLOAT,
    [eps] FLOAT,
    [pe] FLOAT,
    [pb] FLOAT,

    [__createdAt__] VARCHAR(19),
    [__updatedAt__] VARCHAR(19)
);
GO

CREATE TYPE [BotPortfolio].[__processTracking__] AS TABLE (
	[id] BIGINT,
	[createdAt] VARCHAR(19),
	[updatedAt] VARCHAR(19),
	[schemaName] VARCHAR(255),
	[tableName] VARCHAR(255),
	[keyName] VARCHAR(255),
	[keyValue] VARCHAR(255)
)
