CREATE TABLE [BotPortfolio].[accounts] (
    [id] VARCHAR(36) PRIMARY KEY DEFAULT (LOWER(NEWID())),
    [userId] INT NOT NULL,
    [identificationCode] VARCHAR(20),
    [custodyCode] VARCHAR(20),
    [brokerName] VARCHAR(20),
    [brokerInvestorId] VARCHAR(20),
    [brokerAccountId] VARCHAR(20),
    [__createdAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    [__updatedAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    CONSTRAINT FK_user_accounts FOREIGN KEY (userId) REFERENCES [Auth].[users](id) ON DELETE CASCADE
);
GO

CREATE TABLE [BotPortfolio].[balances] (
    [id] VARCHAR(36) PRIMARY KEY DEFAULT (LOWER(NEWID())),
    [accountId] VARCHAR(36) NOT NULL,
    [brokerAccountId] VARCHAR(20),
    [totalCash] INT,
    [availableCash] INT,
    [termDeposit] INT,
    [depositInterest] INT,
    [stockValue] INT,
    [marginableAmount] INT,
    [nonMarginableAmount] INT,
    [totalDebt] INT,
    [netAssetValue] INT,
    [receivingAmount] INT,
    [secureAmount] INT,
    [depositFeeAmount] INT,
    [maxLoanLimit] INT,
    [withdrawableCash] INT,
    [collateralValue] INT,
    [orderSecured] INT,
    [purchasingPower] INT,
    [cashDividendReceiving] INT,
    [marginDebt] FLOAT,
    [marginRate] FLOAT,
    [ppWithdraw] INT,
    [blockMoney] INT,
    [totalRemainDebt] FLOAT,
    [totalUnrealizedDebt] FLOAT,
    [blockedAmount] FLOAT,
    [advancedAmount] INT,
    [advanceWithdrawnAmount] FLOAT,
    [__createdAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    [__updatedAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    CONSTRAINT FK_account_balances FOREIGN KEY (accountId) REFERENCES [Portfolio].[accounts](id) ON DELETE CASCADE
);
GO

CREATE TABLE [BotPortfolio].[orders] (
    [id] VARCHAR(36) PRIMARY KEY DEFAULT (LOWER(NEWID())),
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
    [priceSecure] INT
    [error] VARCHAR(255) DEFAULT NULL,

    [__createdAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    [__updatedAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    CONSTRAINT FK_account_orders FOREIGN KEY (accountId) REFERENCES [Portfolio].[accounts](id) ON DELETE CASCADE
);
GO

CREATE TABLE [BotPortfolio].[deals] (
    [id] VARCHAR(36) PRIMARY KEY DEFAULT (LOWER(NEWID())),
    [accountId] VARCHAR(36) NOT NULL,
    [dealId] VARCHAR(36) NOT NULL,
    [symbol] VARCHAR(10) NOT NULL,
    [brokerAccountId] VARCHAR(20),
    [status] VARCHAR(10),
    [side] VARCHAR(10),
    [accumulateQuantity] INT NOT NULL,
    [closedQuantity] INT NOT NULL,
    [t0ReceivingQuantity] INT,
    [t1ReceivingQuantity] INT,
    [t2ReceivingQuantity] INT,
    [costPrice] INT NOT NULL,
    [averageCostPrice] INT NOT NULL,
    [marketPrice] INT NOT NULL,
    [realizedProfit] INT NOT NULL,
    --     [realizedTotalTaxAndFee] INT,
    --     [collectedBuyingFee] INT,
    --     [collectedBuyingTax] INT,
    --     [collectedStockTransferFee] INT,
    --     [collectedInterestFee] INT,
    --     [estimateRemainTaxAndFee] INT,
    [unrealizedProfit] INT,
    [breakEvenPrice] INT,
    [dividendReceivingQuantity] INT,
    [dividendQuantity] INT,
    [cashReceiving] INT,
    [rightReceivingCash] INT,
    [t0ReceivingCash] INT,
    [t1RecevingCash] INT,
    [t2RecevingCash] INT,
    [createdDate] VARCHAR(30),
    [modifiedDate] VARCHAR(30),

    [__createdAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    [__updatedAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    CONSTRAINT FK_account_deals FOREIGN KEY (accountId) REFERENCES [Portfolio].[accounts](id) ON DELETE CASCADE
);
GO

CREATE TABLE [BotPortfolio].[optimizedWeights] (
    [id] INT IDENTITY(1,1) PRIMARY KEY NOT NULL,
    [date] VARCHAR(10) NOT NULL,
    [symbol] VARCHAR(10) NOT NULL,
    [initialWeight] DECIMAL(8,6) NOT NULL,
    [neutralizedWeight] DECIMAL(8,6) NOT NULL,
    [algorithm] VARCHAR(50) DEFAULT 'CMV',

    [__createdAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    [__updatedAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
);
GO

CREATE TABLE [BotPortfolio].[personalWeights] (
    [id] VARCHAR(36) PRIMARY KEY DEFAULT (LOWER(NEWID())),
    [date] VARCHAR(10) NOT NULL,
    [accountId] VARCHAR(36) NOT NULL,
    [symbol] VARCHAR(10) NOT NULL,
    [targetWeight] DECIMAL(8,6) NOT NULL,
    [actualWeight] DECIMAL(8,6) NOT NULL,

    [__createdAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    [__updatedAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    CONSTRAINT FK_account_portfolio_weights FOREIGN KEY (accountId) REFERENCES [Portfolio].[accounts](id) ON DELETE CASCADE
);
GO

CREATE TABLE [BotPortfolio].[UniverseTopMonthly] (
    [id] INT IDENTITY(1,1) PRIMARY KEY NOT NULL,
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

    [__createdAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    [__updatedAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
);
GO

CREATE TABLE [BotPortfolio].[__processTracking__](
	[id] BIGINT IDENTITY(1,1) NOT NULL,
	[createdAt] VARCHAR(19) DEFAULT (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
	[updatedAt] VARCHAR(19) DEFAULT (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
	[schemaName] VARCHAR(255) NOT NULL,
	[tableName] VARCHAR(255) NOT NULL,
	[keyName] VARCHAR(255) NOT NULL,
	[keyValue] VARCHAR(255),
	PRIMARY KEY CLUSTERED (id ASC),
	UNIQUE (schemaName,tableName)
)