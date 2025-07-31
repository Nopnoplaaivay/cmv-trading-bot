CREATE TYPE [BotBrokers].[tradingTokens] AS TABLE(
	[id] VARCHAR(36),
    [account] VARCHAR(255),
	[jwtToken] VARCHAR(2048),
	[tradingToken] VARCHAR(255),
	[broker] VARCHAR(20),
	[createdAt] VARCHAR(19),
	[updatedAt] VARCHAR(19)
)