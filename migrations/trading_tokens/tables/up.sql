CREATE TABLE [BotBrokers].[tradingTokens](
	[id] VARCHAR(36) PRIMARY KEY DEFAULT (LOWER(NEWID())),
    [account] VARCHAR(255) NOT NULL,
	[jwtToken] VARCHAR(2048) NOT NULL,
	[tradingToken] VARCHAR(255),
	[broker] VARCHAR(20) DEFAULT ('DNSE') NOT NULL,
	[createdAt] VARCHAR(19) DEFAULT (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
	[updatedAt] VARCHAR(19) DEFAULT (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
	UNIQUE (tradingToken,broker)
)