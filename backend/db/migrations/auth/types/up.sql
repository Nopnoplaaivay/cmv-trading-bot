CREATE TYPE [BotAuth].[users] AS TABLE(
    [id] INT,
    [account] VARCHAR(255),
    [password] VARCHAR(255),
    [mobile] VARCHAR(15),
    [email] VARCHAR(50),
    [role] VARCHAR(50),
    [__createdAt__] VARCHAR(19),
    [__updatedAt__] VARCHAR(19)
);
GO

CREATE TYPE [BotAuth].[sessions] AS TABLE(
    [id] VARCHAR(36),
    [signature] VARCHAR(255),
    [expires_at] DATETIME,
    [role] VARCHAR(10),
    [userId] INT,
    [__createdAt__] VARCHAR(19),
    [__updatedAt__] VARCHAR(19)
);
GO