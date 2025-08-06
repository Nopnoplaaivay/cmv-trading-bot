CREATE TABLE [BotPortfolio].[accounts] (
    [id] VARCHAR(36) PRIMARY KEY DEFAULT (LOWER(NEWID())),
    [userId] INT NOT NULL,
    [name] NVARCHAR(50) NOT NULL,
    [accountType] VARCHAR(20) NULL,
    [identificationCode] VARCHAR(20),
    [custodyCode] VARCHAR(20) NOT NULL,
    [password] VARCHAR(255) NOT NULL,
    [brokerName] VARCHAR(20),
    [brokerInvestorId] VARCHAR(20),
    [brokerAccountId] VARCHAR(20) UNIQUE,
    [__createdAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    [__updatedAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    CONSTRAINT FK_user_accounts FOREIGN KEY (userId) REFERENCES [BotAuth].[users](id) ON DELETE CASCADE,
    CONSTRAINT UQ_brokerAccountId UNIQUE ([brokerAccountId])
);
GO

CREATE TABLE [BotPortfolio].[balances] (
    [id] VARCHAR(36) PRIMARY KEY DEFAULT (LOWER(NEWID())),
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
    [advanceWithdrawnAmount] FLOAT,
    [advancedAmount] BIGINT,
    [blockedAmount] FLOAT,
    [__createdAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    [__updatedAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    CONSTRAINT FK_account_balances FOREIGN KEY (brokerAccountId) REFERENCES [BotPortfolio].[accounts](brokerAccountId) ON DELETE CASCADE
);
GO

CREATE TABLE [BotPortfolio].[deals] (
    [id] VARCHAR(36) PRIMARY KEY DEFAULT (LOWER(NEWID())),
    [brokerAccountId] VARCHAR(20) NOT NULL,
    [dealId] VARCHAR(10) NOT NULL,
    [symbol] VARCHAR(10) NOT NULL,
    [status] VARCHAR(10),
    [side] VARCHAR(10),
    [secure] FLOAT,
    [accumulateQuantity] BIGINT NOT NULL,
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

    [__createdAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    [__updatedAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    CONSTRAINT FK_account_deals FOREIGN KEY (brokerAccountId) REFERENCES [BotPortfolio].[accounts](brokerAccountId) ON DELETE CASCADE
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
    [priceSecure] INT,
    [error] VARCHAR(255) DEFAULT NULL,

    [__createdAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    [__updatedAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    CONSTRAINT FK_account_orders FOREIGN KEY (accountId) REFERENCES [BotPortfolio].[accounts](id) ON DELETE CASCADE
);
GO

CREATE TABLE [BotPortfolio].[optimizedWeights] (
    [id] INT IDENTITY(1,1) PRIMARY KEY NOT NULL,
    [date] VARCHAR(10) NOT NULL,
    [symbol] VARCHAR(10) NOT NULL,
    [marketPrice] FLOAT NOT NULL,
    [initialWeight] DECIMAL(8,6) NOT NULL,
    [neutralizedWeight] DECIMAL(8,6) NOT NULL,
    [limitedWeight] DECIMAL(8,6) NULL,
    [neutralizedLimitedWeight] DECIMAL(8,6) NULL,
    [algorithm] VARCHAR(50) DEFAULT 'CMV',

    [__createdAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    [__updatedAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
);
GO

CREATE TABLE [BotPortfolio].[UniverseTopMonthly](
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