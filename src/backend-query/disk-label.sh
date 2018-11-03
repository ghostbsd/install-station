#!/bin/sh
#-
# Copyright (c) 2018 iXsystems, Inc.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#
# $FreeBSD: $

# Query mbr partitions label and display them
##############################

. ${PROGDIR}/backend/functions.sh
. ${PROGDIR}/backend/functions-disk.sh


if [ -z "${1}" ]
then
  echo "Error: No partition specified!"
  exit 1
fi

if [ ! -e "/dev/${1}" ]
then
  echo "Error: Partition /dev/${1} does not exist!"
  exit 1
fi


DISK="${1}"
TMPDIR=${TMPDIR:-"/tmp"}
# Display if this is GPT or MBR formatted
gpart show ${1} | grep "GPT" >/dev/null 2>/dev/null
if [ "$?" = "0" ] ; then
    #echo "${1}-format: GPT"
    TYPE="GPT"
else
    #echo "${1}-format: MBR"
    TYPE="MBR"
fi

if [ "$TYPE" = "MBR" ] ; then
    sp="s"
else
    sp="p"
fi

# Get a listing of partitions on this disk
gpart show ${DISK} | grep -v ${DISK} | tr -s '\t' ' ' | cut -d ' ' -f 4,3,5 >${TMPDIR}/disk-${DISK}
while read i
do

    if [ ! -z "${i}" ] ; then
        BLOCK="`echo ${i} | cut -d ' ' -f 1`"
        MB="`expr ${BLOCK} / 2048`MB"
    fi
    if [ ! "${MB}" = "0MB" ] ; then
        LABEL="`echo ${i} | cut -d ' ' -f 3`"
        SLICE="`echo ${i} | cut -d ' ' -f 2`"
        if [ "$SLICE" = '-' ] ; then
            echo "freespace  ${MB}"
        else
            if [ ! -z "$SLICE" ] ; then
                echo "${MB} ${LABEL}"
            fi
        fi
    fi

done <${TMPDIR}/disk-${DISK}
