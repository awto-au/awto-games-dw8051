#include "UserCommonInclude.h"
#include "AwtoApps.h"
#include "arcade.h"

// Game sound sequencer over AwtoAppSoundTone (the player that remains in awto-ddc plays one tone per call).
// Notes, tracks and cmd ids: scripts/pacman_sound.py -> arcade_snd_data.inc (pairs {sc | octave flag, 10 ms ticks}, 0 ticks = end).
// User mute (VCP 0x8D) keeps the sequencer running and the tone calls off. One tone at a time: a new track plays when its priority >= the playing one's; waka and the background state resume when it ends.
#define ARC_SND_OCT_MASK                        0x7F                // note byte bit 7 = octave flag, passed on to the tone call
#define ARC_SND_TICK_MS                         10
#define ARC_SND_GAP_MS                          4                   // AwtoPmSoundTone adds this pitch gap to the length it is given (fw/audio/audio.c AWTO_PS_GAP_MS)
#define ARC_SND_TRACK_NONE                      0xFE
#define ARC_SND_TRACK_WAKA                      1
#define ARC_SND_TRACK_BG0                       6                   // background state 1..6 = tracks 6..11 (siren 1..3, frightened, thrust, saucer)
#define ARC_SND_TRACK_BG_LAST                   11
#define ARC_SND_PRIO_TOP                        7
#define ARC_SND_CMD_WAKA                        1                   // cmd ids of pacman_sound.py CMDS
#define ARC_SND_CMD_STOP                        4
#define ARC_SND_CMD_WAKA_OFF                    8
#define AWTO_PS_TRACK_NONE                      ARC_SND_TRACK_NONE  // the generated table names it
#define ARC_SND_F_WAKA                          0x04                // flags: eating, waka wanted
#define ARC_SND_F_BG_SHIFT                      4                   // flags 7:4 = background state wanted
#define ARC_SND_F_LOW_MASK                      0x0F
#define ARC_SND_NOTE_BYTES                      2
#define ARC_SND_TRK_SHIFT                       2                   // track row = 4 bytes: offset lo, offset hi, priority, loops
#define ARC_SND_TRK_PRIO                        2
#define ARC_SND_TRK_LOOPS                       3
#define ARC_SND_CMD_ROW                         3                   // cmd row = 3 bytes: track, 0, 1 = event value is the cmd
#define ARC_SND_RESYNC_MS                       125                 // a note later than this behind its schedule restarts the schedule (a long pass: no burst of notes)
#include "arcade_snd_data.inc"

#pragma place bank(13)
static BYTE SndByte(WORD usIdx)
{
    return g_aucArcSndData[usIdx];
}

__xdata BYTE g_ucArcSndTrack;                                      // playing track, ARC_SND_TRACK_NONE = silent
__xdata WORD g_usArcSndPos;
__xdata WORD g_usArcSndAt;                                         // AwtoMs low word at the current note's start
__xdata WORD g_usArcSndDur;                                        // current note length, ms
__xdata BYTE g_ucArcSndFlags;
__xdata BYTE g_ucArcSndPlayed;                                     // the current note's tone call went through (a refused one is retried)

static BYTE SndTrk(BYTE ucTrack, BYTE ucField)
{
    return SndByte(AWTO_PS_TRK + ((WORD)ucTrack << ARC_SND_TRK_SHIFT) + ucField);
}

static WORD SndOff(BYTE ucTrack)
{
    return (WORD)SndTrk(ucTrack, 0) | ((WORD)SndTrk(ucTrack, 1) << 8);
}

static BYTE SndPrio(BYTE ucTrack)
{
    return SndTrk(ucTrack, ARC_SND_TRK_PRIO);
}

static void SndStart(BYTE ucTrack)
{
    if(g_ucArcSndTrack != ARC_SND_TRACK_NONE)
    {
        AwtoAppSoundStop();                                         // the replaced track's tone ends now, the new one starts on the next pass
    }
    g_ucArcSndTrack = ucTrack;
    g_usArcSndPos = SndOff(ucTrack);
    g_usArcSndAt = (WORD)AwtoAppMs();
    g_usArcSndDur = 0;
    g_ucArcSndPlayed = 1;                                                 // nothing pending: the first note is due at once
}

static void SndResume(void)                                         // after a sound ended: waka if eating, else the background sound, else silence
{
    BYTE ucBg = g_ucArcSndFlags >> ARC_SND_F_BG_SHIFT;

    if((g_ucArcSndFlags & ARC_SND_F_WAKA) != 0)
    {
        SndStart(ARC_SND_TRACK_WAKA);
    }
    else if(ucBg != 0)
    {
        SndStart(ARC_SND_TRACK_BG0 - 1 + ucBg);
    }
    else
    {
        g_ucArcSndTrack = ARC_SND_TRACK_NONE;
    }
}

static void SndRequest(BYTE ucTrack)
{
    if((g_ucArcSndTrack == ARC_SND_TRACK_NONE) || (SndPrio(ucTrack) >= SndPrio(g_ucArcSndTrack)))
    {
        SndStart(ucTrack);
    }
}

void ArcSndPoll(void)                                               // once per step
{
    BYTE ucDur;
    BYTE ucNote;
    WORD usNow = (WORD)AwtoAppMs();
    WORD usLate = usNow - g_usArcSndAt;                                   // ms since the current note's scheduled start

    if((g_ucArcSndTrack == ARC_SND_TRACK_NONE) || (usLate >= ARC_MS_HALF) || ((g_ucArcSndPlayed != 0) && (usLate < g_usArcSndDur)))
    {
        return;
    }
    if(g_ucArcSndPlayed != 0)                                             // the current note has run its length: the next one
    {
        g_usArcSndAt += g_usArcSndDur;
        if((WORD)(usNow - g_usArcSndAt) >= ARC_SND_RESYNC_MS)
        {
            g_usArcSndAt = usNow;
        }
        ucDur = SndByte(g_usArcSndPos + 1);
        if((ucDur == 0) && (SndTrk(g_ucArcSndTrack, ARC_SND_TRK_LOOPS) != 0))
        {
            g_usArcSndPos = SndOff(g_ucArcSndTrack);
            ucDur = SndByte(g_usArcSndPos + 1);
        }
        if(ucDur == 0)
        {
            SndResume();
            return;
        }
        g_usArcSndDur = (WORD)ucDur * ARC_SND_TICK_MS;
        g_ucArcSndPlayed = 0;
    }
    ucNote = SndByte(g_usArcSndPos);
    if(((ucNote & ARC_SND_OCT_MASK) != 0) && (GET_OSD_VOLUME_MUTE() == 0) && (AwtoAppSoundTone(ucNote, g_usArcSndDur - ARC_SND_GAP_MS) == AWTO_TONE_BUSY))
    {
        return;                                                     // the last tone still runs: asked again next pass, the note keeps its place
    }
    g_ucArcSndPlayed = 1;
    g_usArcSndPos += ARC_SND_NOTE_BYTES;
}

void ArcSndBg(BYTE ucState)                                         // background state (siren speed 1..3, frightened 4, thrust 5, saucer 6, 0 none): acts on a change
{
    if((g_ucArcSndFlags >> ARC_SND_F_BG_SHIFT) == ucState)
    {
        return;
    }
    g_ucArcSndFlags = (g_ucArcSndFlags & ARC_SND_F_LOW_MASK) | (BYTE)(ucState << ARC_SND_F_BG_SHIFT);
    if((g_ucArcSndTrack == ARC_SND_TRACK_NONE) || ((g_ucArcSndTrack >= ARC_SND_TRACK_BG0) && (g_ucArcSndTrack <= ARC_SND_TRACK_BG_LAST)))
    {
        SndResume();
    }
}

void ArcSndInit(void)                                               // app start: silent, nothing wanted (XDATA starts zeroed = track 0)
{
    g_ucArcSndFlags = 0;
    g_ucArcSndTrack = ARC_SND_TRACK_NONE;
}

void ArcSndStop(void)
{
    ArcSndInit();
    AwtoAppSoundStop();
}

void ArcSnd(BYTE ucCmd)
{
    WORD usRow;

    if(ucCmd >= AWTO_PS_CMDS)
    {
        return;
    }
    if(ucCmd == ARC_SND_CMD_WAKA_OFF)
    {
        g_ucArcSndFlags &= (BYTE)~ARC_SND_F_WAKA;
        if(g_ucArcSndTrack == ARC_SND_TRACK_WAKA)
        {
            SndResume();
        }
        return;
    }
    if(ucCmd == ARC_SND_CMD_STOP)
    {
        ArcSndStop();
        return;
    }
    if(ucCmd == ARC_SND_CMD_WAKA)
    {
        g_ucArcSndFlags |= ARC_SND_F_WAKA;
    }
    else
    {
        g_ucArcSndFlags &= (BYTE)~ARC_SND_F_WAKA;                         // any other sound ends the eating run; the next pellet starts waka again
    }
    usRow = AWTO_PS_CMD + ucCmd * ARC_SND_CMD_ROW;
    SndRequest(SndByte(usRow));
}
