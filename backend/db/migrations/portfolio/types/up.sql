CREATE TYPE [BotPortfolio].[__processTracking__] AS TABLE (
	[id] BIGINT,
	[createdAt] VARCHAR(19),
	[updatedAt] VARCHAR(19),
	[schemaName] VARCHAR(255),
	[tableName] VARCHAR(255),
	[keyName] VARCHAR(255),
	[keyValue] VARCHAR(255)
)

CREATE TYPE [BotPortfolio].[optimizedWeights] AS TABLE(
    [id] INT,
    [date] VARCHAR(10) NOT NULL,
    [symbol] VARCHAR(10) NOT NULL,
    [initialWeight] DECIMAL(8,6) NOT NULL,
    [neutralizedWeight] DECIMAL(8,6),
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
