/*
 *                            COPYRIGHT
 *
 *  exponentialrv.c
 *  Copyright (C) 2014 Exstrom Laboratories LLC
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  A copy of the GNU General Public License is available on the internet at:
 *  http://www.gnu.org/copyleft/gpl.html
 *
 *  or you can write to:
 *
 *  The Free Software Foundation, Inc.
 *  675 Mass Ave
 *  Cambridge, MA 02139, USA
 *
 *  Exstrom Laboratories LLC contact:
 *  stefan(AT)exstrom.com
 *
 *  Exstrom Laboratories LLC
 *  Longmont, CO 80503, USA
 *
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

int main(int argc, char *argv[]) {
  if (argc < 3) {
    printf("usage: %s n lambda seed\n", argv[0]);
    printf("  Generates n random numbers from the exponential distribution\n");
    printf("  f(x) = lambda * exp(-lambda * x)\n");
    printf("  seed = optional random number seed\n");
    exit(-1);
  }

  unsigned long i, n = strtoul(argv[1], NULL, 10);
  double lambda = strtod(argv[2], NULL);
  unsigned int seed = argc > 3 ? strtoul(argv[3], NULL, 10) : time(NULL);
  double u;

  srand(seed);

  for (i = 0; i < n; ++i) {
    u = (double)rand() / RAND_MAX;
    printf("%lf ", -log(u) / lambda);
  }

  return (0);
}