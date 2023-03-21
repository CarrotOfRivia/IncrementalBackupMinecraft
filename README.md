# Incremental Backup Minecraft Server Using FTPS

## Motivation
As the owner of a personal Minecraft server, I once woke up to find that someone had destroyed my entire base overnight. I was frustrated to discover that the automatic backup by my service provider only ran once a day, meaning that I had lost hours of progress since the last backup.

That's when it hit me - what if I could set up a more frequent backup schedule? And luckily, my servise offers a FTPS interface which makes it possible for me to interact with server files directly through scripts. Combined with incremental backup strategy, I can backup my server every hour without worrying about running out of storage space.

## Implementation
I used the [`ftplib`](https://docs.python.org/3/library/ftplib.html) package in Python to transfer files between my server and local machine. Here's an overview:

1. The first run creates a full backup of every file on the server and saves the modification time of each file as a dictionary.
2. For subsequent runs, only the files with modifications since the previous run are downloaded from the server via FTP. The modification dictionary is updated each time.
3. For every `24*7` runs (one week), the working directory is compressed, the compressed file is saved, and the working directory is cleaned up.
4. The process then repeats from step 1.

The script `run_backup.sh` performs a single run and I am able to use `crontab` to execute the script every hour.

## Results
The backup works as expected:

```
$ ls workdir/ | tail
...
backup_2023-03-20_13-15-01
backup_2023-03-20_14-15-01
backup_2023-03-20_15-15-02
backup_2023-03-20_16-15-01
backup_2023-03-20_17-15-01
backup_2023-03-20_18-15-01
backup_2023-03-20_19-15-01
backup_2023-03-20_20-15-01
backup_2023-03-20_21-15-02
modify.yaml
```

# Analysis
By doing `du -sh workdir/*`, I got:
```
1.4G    workdir/backup_2023-03-18_00-03-14
...
101M    workdir/backup_2023-03-18_09-15-02
100M    workdir/backup_2023-03-18_10-15-01
...
72M     workdir/backup_2023-03-18_21-15-01
8.6M    workdir/backup_2023-03-18_22-15-01
8.6M    workdir/backup_2023-03-18_23-15-01
8.6M    workdir/backup_2023-03-19_00-15-01
65M     workdir/backup_2023-03-19_01-15-02
8.6M    workdir/backup_2023-03-19_02-15-02
8.6M    workdir/backup_2023-03-19_03-15-02
8.6M    workdir/backup_2023-03-19_04-15-01
8.6M    workdir/backup_2023-03-19_05-15-01
8.6M    workdir/backup_2023-03-19_06-15-01
8.6M    workdir/backup_2023-03-19_07-15-01
```
So the whole server is 1.4 GB. The increment is only 8.6 MB if no player is online during the hour. As a result, I can easily monitor the player activity here.

```
$ cat workdir/backup_2023-03-18_21-15-01/logs/latest.log | grep joined
[08:26:50] [Server thread/INFO]: ### joined the game
[09:20:04] [Server thread/INFO]: ### joined the game
[09:46:56] [Server thread/INFO]: ### joined the game
[14:37:49] [Server thread/INFO]: ### joined the game
[21:02:01] [Server thread/INFO]: ### joined the game
```
