CREATE TABLE [BotAuth].[users] (
    [id] INT IDENTITY(1,1) PRIMARY KEY NOT NULL,
    [account] VARCHAR(255) UNIQUE NOT NULL,
    [password] VARCHAR(255) NOT NULL,
    [mobile] VARCHAR(15),
    [email] VARCHAR(50),
    [role] VARCHAR(50) DEFAULT 'free' NOT NULL,
    [__createdAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    [__updatedAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
);
GO

CREATE TABLE [BotAuth].[sessions] (
    [id] VARCHAR(36) PRIMARY KEY DEFAULT (LOWER(NEWID())),
    [signature] VARCHAR(255) NOT NULL,
    [expires_at] DATETIME NOT NULL,
    [role] VARCHAR(10) default 'free' NOT NULL,
    [userId] INT NOT NULL,
    [__createdAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    [__updatedAt__] VARCHAR(19) default (format(switchoffset(sysutcdatetime(),'+07:00'),'yyyy-MM-dd HH:mm:ss')) NOT NULL,
    CONSTRAINT FK_user_sessions FOREIGN KEY (userId) REFERENCES [BotAuth].[users](id) ON DELETE CASCADE
);
GO