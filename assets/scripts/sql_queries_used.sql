USE mvp_db;
GO
-- Create the production-ready table "mvp_career_stats" without the Awards column
CREATE TABLE dbo.mvp_career_stats (
   Player          VARCHAR(100)    NOT NULL,
   Season          CHAR(7)         NOT NULL,  -- Format: yyyy-yy (e.g., "2015-16")
   Age             INT,
   Team            VARCHAR(50),
   Lg              VARCHAR(50),
   Pos             VARCHAR(10),
   G               INT,
   GS              INT,
   MP              FLOAT,
   FG              FLOAT,
   FGA             FLOAT,
   [FG%]           FLOAT,
   [3P]            FLOAT,
   [3PA]           FLOAT,
   [3P%]           FLOAT,
   [2P]            FLOAT,
   [2PA]           FLOAT,
   [2P%]           FLOAT,
   [eFG%]          FLOAT,
   FT              FLOAT,
   FTA             FLOAT,
   [FT%]           FLOAT,
   ORB             FLOAT,
   DRB             FLOAT,
   TRB             FLOAT,
   AST             FLOAT,
   STL             FLOAT,
   BLK             FLOAT,
   TOV             FLOAT,
   PF              FLOAT,
   PTS             FLOAT,
   MVP_Award_Year    NVARCHAR(7),   -- Format: 'YYYY-YY'
   PlayerPhoto       NVARCHAR(255), -- URL for player's headshot
   TeamLogo          NVARCHAR(255)  -- URL for team logo
);
GO
-- Insert clean, transformed data from dbo.mvp_data into dbo.mvp_career_stats.
-- (Note: We assume dbo.mvp_data’s column names follow the CSV header normalization.)
INSERT INTO dbo.mvp_career_stats (
   Player, Season, Age, Team, Lg, Pos, G, GS, MP, FG, FGA, [FG%],
   [3P], [3PA], [3P%], [2P], [2PA], [2P%], [eFG%], FT, FTA, [FT%],
   ORB, DRB, TRB, AST, STL, BLK, TOV, PF, PTS, MVP_Award_Year, PlayerPhoto, TeamLogo
)
SELECT
   Player,
   Season,
   TRY_CAST(Age AS INT) AS Age,
   Team,
   Lg,
   Pos,
   TRY_CAST(G AS INT) AS G,
   TRY_CAST(GS AS INT) AS GS,
   TRY_CAST(MP AS FLOAT) AS MP,
   TRY_CAST(FG AS FLOAT) AS FG,
   TRY_CAST(FGA AS FLOAT) AS FGA,
   TRY_CAST([FG1] AS FLOAT) AS [FG%],
   TRY_CAST([_3P] AS FLOAT) AS [3P],
   TRY_CAST([_3PA] AS FLOAT) AS [3PA],
   TRY_CAST([_3P1] AS FLOAT) AS [3P%],
   TRY_CAST([_2P] AS FLOAT) AS [2P],
   TRY_CAST([_2PA] AS FLOAT) AS [2PA],
   TRY_CAST([_2P1] AS FLOAT) AS [2P%],
   TRY_CAST([eFG] AS FLOAT) AS [eFG%],
   TRY_CAST(FT AS FLOAT) AS FT,
   TRY_CAST(FTA AS FLOAT) AS FTA,
   TRY_CAST([FT1] AS FLOAT) AS [FT%],
   TRY_CAST(ORB AS FLOAT) AS ORB,
   TRY_CAST(DRB AS FLOAT) AS DRB,
   TRY_CAST(TRB AS FLOAT) AS TRB,
   TRY_CAST(AST AS FLOAT) AS AST,
   TRY_CAST(STL AS FLOAT) AS STL,
   TRY_CAST(BLK AS FLOAT) AS BLK,
   TRY_CAST(TOV AS FLOAT) AS TOV,
   TRY_CAST(PF AS FLOAT) AS PF,
   TRY_CAST(PTS AS FLOAT) AS PTS,
   MVP_Award_Year,
   PlayerPhoto,
   TeamLogo
FROM dbo.mvp_data
WHERE TRY_CAST(G AS INT) > 0;  -- Exclude rows where the player did not play any games.
GO

-- Data Quality & Validation Checks
-- 1. Row Count Check
SELECT COUNT(*) AS StagingRowCount FROM dbo.mvp_data;
SELECT COUNT(*) AS ProductionRowCount FROM dbo.mvp_career_stats;
GO

-- 2. Duplicate Check by Player and Season
SELECT Player, Season, COUNT(*) AS Occurrence
FROM dbo.mvp_career_stats
GROUP BY Player, Season
HAVING COUNT(*) > 1;
GO

-- 3. Data Type and Range Checks (example: Age, FG%, FT%)
SELECT *
FROM dbo.mvp_career_stats
WHERE Age > 18 OR Age < 50
  OR [FG%] < 0 OR [FG%] > 1
  OR [FT%] < 0 OR [FT%] > 1
ORDER BY Season DESC;
GO

-- 4. Null Checks in Critical Columns
SELECT *
FROM dbo.mvp_career_stats
WHERE Player IS NULL OR Season IS NULL;
GO

-- Create the view to be loaded in Power BI
CREATE VIEW dbo.vw_mvp_career_stats AS
SELECT * FROM dbo.mvp_career_stats;
GO