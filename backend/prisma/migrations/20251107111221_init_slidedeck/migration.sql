-- CreateEnum
CREATE TYPE "visual_theme" AS ENUM ('MINIMALIST', 'CHALKBOARD', 'CORPORATE', 'MODERN', 'GRADIENT');

-- CreateEnum
CREATE TYPE "video_status" AS ENUM ('PENDING', 'GENERATING_CONTENT', 'CREATING_SLIDES', 'FETCHING_IMAGES', 'GENERATING_AUDIO', 'ASSEMBLING_VIDEO', 'COMPLETED', 'FAILED');

-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "lectures" (
    "id" TEXT NOT NULL,
    "topic" TEXT NOT NULL,
    "targetAudience" TEXT,
    "desiredLength" INTEGER NOT NULL,
    "visualTheme" "visual_theme" NOT NULL DEFAULT 'MINIMALIST',
    "videoUrl" TEXT,
    "slidesPdfUrl" TEXT,
    "videoStatus" "video_status" NOT NULL DEFAULT 'PENDING',
    "processingStartedAt" TIMESTAMP(3),
    "processingCompletedAt" TIMESTAMP(3),
    "errorMessage" TEXT,
    "userId" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "lectures_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "slides" (
    "id" TEXT NOT NULL,
    "lectureId" TEXT NOT NULL,
    "slideNumber" INTEGER NOT NULL,
    "title" TEXT NOT NULL,
    "bulletPoints" TEXT[],
    "speakerNotes" TEXT NOT NULL,
    "imageUrl" TEXT,
    "imageQuery" TEXT,
    "imageAttribution" TEXT,
    "audioUrl" TEXT,
    "audioDuration" DOUBLE PRECISION,
    "slideImageUrl" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "slides_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "quiz_questions" (
    "id" TEXT NOT NULL,
    "lectureId" TEXT NOT NULL,
    "questionNumber" INTEGER NOT NULL,
    "questionText" TEXT NOT NULL,
    "options" TEXT[],
    "correctAnswer" INTEGER NOT NULL,
    "explanation" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "quiz_questions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "slide_decks" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "topic" TEXT NOT NULL,
    "audience" TEXT,
    "durationMinutes" INTEGER NOT NULL,
    "theme" TEXT NOT NULL,
    "format" TEXT NOT NULL,
    "slideCount" INTEGER NOT NULL,
    "status" TEXT NOT NULL,
    "r2Key" TEXT NOT NULL,
    "r2Bucket" TEXT NOT NULL,
    "fileSizeBytes" INTEGER,
    "checksum" TEXT,
    "coverThumbR2Key" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "slide_decks_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "deck_slides" (
    "id" TEXT NOT NULL,
    "deckId" TEXT NOT NULL,
    "index" INTEGER NOT NULL,
    "heading" TEXT NOT NULL,
    "bullets" JSONB NOT NULL,
    "speakerNotes" TEXT NOT NULL,
    "imageQuery" TEXT,
    "imageR2Key" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "deck_slides_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "generation_jobs" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "deckId" TEXT,
    "status" TEXT NOT NULL,
    "progressPct" INTEGER NOT NULL DEFAULT 0,
    "errorCode" TEXT,
    "errorMessage" TEXT,
    "startedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "endedAt" TIMESTAMP(3),

    CONSTRAINT "generation_jobs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "asset_attributions" (
    "id" TEXT NOT NULL,
    "deckId" TEXT NOT NULL,
    "slideIndex" INTEGER NOT NULL,
    "source" TEXT NOT NULL,
    "authorName" TEXT NOT NULL,
    "imageUrl" TEXT NOT NULL,
    "license" TEXT,

    CONSTRAINT "asset_attributions_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE INDEX "lectures_userId_idx" ON "lectures"("userId");

-- CreateIndex
CREATE INDEX "lectures_videoStatus_idx" ON "lectures"("videoStatus");

-- CreateIndex
CREATE INDEX "lectures_createdAt_idx" ON "lectures"("createdAt");

-- CreateIndex
CREATE INDEX "slides_lectureId_idx" ON "slides"("lectureId");

-- CreateIndex
CREATE UNIQUE INDEX "slides_lectureId_slideNumber_key" ON "slides"("lectureId", "slideNumber");

-- CreateIndex
CREATE INDEX "quiz_questions_lectureId_idx" ON "quiz_questions"("lectureId");

-- CreateIndex
CREATE UNIQUE INDEX "quiz_questions_lectureId_questionNumber_key" ON "quiz_questions"("lectureId", "questionNumber");

-- CreateIndex
CREATE INDEX "slide_decks_userId_idx" ON "slide_decks"("userId");

-- CreateIndex
CREATE INDEX "deck_slides_deckId_idx" ON "deck_slides"("deckId");

-- CreateIndex
CREATE INDEX "generation_jobs_userId_idx" ON "generation_jobs"("userId");

-- CreateIndex
CREATE INDEX "generation_jobs_deckId_idx" ON "generation_jobs"("deckId");

-- AddForeignKey
ALTER TABLE "lectures" ADD CONSTRAINT "lectures_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "slides" ADD CONSTRAINT "slides_lectureId_fkey" FOREIGN KEY ("lectureId") REFERENCES "lectures"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "quiz_questions" ADD CONSTRAINT "quiz_questions_lectureId_fkey" FOREIGN KEY ("lectureId") REFERENCES "lectures"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "slide_decks" ADD CONSTRAINT "slide_decks_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "deck_slides" ADD CONSTRAINT "deck_slides_deckId_fkey" FOREIGN KEY ("deckId") REFERENCES "slide_decks"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "generation_jobs" ADD CONSTRAINT "generation_jobs_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "generation_jobs" ADD CONSTRAINT "generation_jobs_deckId_fkey" FOREIGN KEY ("deckId") REFERENCES "slide_decks"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "asset_attributions" ADD CONSTRAINT "asset_attributions_deckId_fkey" FOREIGN KEY ("deckId") REFERENCES "slide_decks"("id") ON DELETE CASCADE ON UPDATE CASCADE;
