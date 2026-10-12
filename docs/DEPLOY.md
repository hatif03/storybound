# Deployment (AWS, hackathon account)

Written Mon 12 Oct 2026. This is a plain single-server deployment for judges. It is **http only** (no certificate, no domain), **tracing is off** (no `NEATLOGS_*` variables on the server, so nothing a visitor uploads reaches neatlogs), and the app currently does NOT tell visitors anything about not uploading a real child's photo (its Grown-ups page only says the drawing is sent to the server): add that sentence to the web app or the share message. No secret is in this file.

## URLs

- App: http://ec2-34-237-142-143.compute-1.amazonaws.com/
- Free demo mode (needs no models, runs in the browser): http://ec2-34-237-142-143.compute-1.amazonaws.com/?mock=1
- The public DNS name changes if the instance is stopped and started (no Elastic IP, on purpose).

## Status (final)

- **Everything works end to end, checked from outside.** `/api/health`, `/api/lessons`, `/api/fixtures`, the home page, `/?mock=1` (and `web/scripts/e2e-quiz-mock.mjs --url <app url>`: "problems: none").
- **One real story** (benign/bunny-bow-carrot, sharing, pictures=auto, 12 Oct about 18:20 IST): `run.finished`, 335 s, first page after 65 s, receipt "27 promises checked. 5 pages rewritten. 1 could not be fully kept: quiz_reading_level" (28 promises, 26 kept, 0 shipped violations), estimated cost $0.21 (4 pictures; the agent chose which pages to paint), all 8 pages narrated (MP3 served), page pictures served where painted and 410 where deliberately not painted. Then **one read-along movie** from that story: done in 227 s, 33 MB MP4, about 3 min 47 s. The story was then deleted (204, later calls 404). One more real story is still unspent from the allowance of two.
- Google access is **keyless**: Workload Identity Federation (below). The organisation policy that blocks service-account keys was left as it is, and no key exists anywhere.
- Not verified: behaviour under the daily caps (not hit), two stories at once (`STORYBOUND_MAX_RUNS=2`), and a movie render while a story runs (a render uses most of the 2 vCPUs and 2 GB: expect slow pages if both happen together).

## How Google access works (no key)

The instance has an AWS IAM role with **no permissions** (`storybound-demo-role`, instance profile of the same name). The app uses a credential file `/etc/storybound/gcp-wif.json` (`external_account`; it holds only the audience and URLs, no secret). The Google client signs an AWS `GetCallerIdentity` request with the role's temporary credentials from the instance metadata service (IMDSv2), exchanges it at Google STS and impersonates the service account `storybound-demo@project-f0b6b4ce-541f-43ff-9f7.iam.gserviceaccount.com` (short-lived tokens).

- Workload identity pool `storybound-demo-pool` (global), AWS provider `storybound-demo-aws` for account 082229155652.
- Attribute condition: `assertion.arn.startsWith('arn:aws:sts::082229155652:assumed-role/storybound-demo-role/')`, so no other role in the shared AWS account can use the pool. Mapping: `google.subject=assertion.arn`, `attribute.aws_role=assertion.arn.split('/')[1]`.
- `roles/iam.workloadIdentityUser` on the service account is granted only to `principalSet://iam.googleapis.com/projects/147606977567/locations/global/workloadIdentityPools/storybound-demo-pool/attribute.aws_role/storybound-demo-role` (not the whole pool, not allUsers).
- Service account roles: `roles/aiplatform.user`, `roles/serviceusage.serviceUsageConsumer`. Text-to-Speech needed nothing more (narration worked).
- APIs enabled on the project for this: `iamcredentials.googleapis.com`, `sts.googleapis.com`.
- Test on the server: `sudo -u storybound env GOOGLE_APPLICATION_CREDENTIALS=/etc/storybound/gcp-wif.json /opt/storybound/.venv/bin/python -c "import google.auth,google.auth.transport.requests as r; c,_=google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform']); c.refresh(r.Request()); print(bool(c.token))"`

## What was created

| Thing | Value |
| --- | --- |
| AWS account / region / profile | 082229155652, us-east-1, `neathack` (IAM user hackathon-user-029) |
| EC2 instance | `i-0ffe97be19c22a88c`, t3.small, Ubuntu 24.04 LTS amd64 (AMI `ami-0fa5967347d08d2df`, 4 Oct 2026 build), 20 GB gp3 root volume, IMDSv2 required, 2 GB swap file |
| Network | the account's shared "Hackathon_VPC" (there is no default VPC), public subnet `subnet-01e42aa06c14b3be1` (us-east-1a), public IP assigned at launch, no Elastic IP |
| Security group | `sg-09e65b4a89aef1304` (`storybound-demo`): TCP 80 from anywhere; TCP 22 only from the builder's IP at launch time (`/32`; if your IP changes, update that rule) |
| Key pair | name `storybound-demo` (private key on the builder's machine at `C:\Users\mdhat\.ssh\storybound-demo.pem`, not in the repo) |
| Tags | `Name=storybound-demo`, `Project=storybound` on the instance, volume, security group and key pair |
| Google service account | `storybound-demo@project-f0b6b4ce-541f-43ff-9f7.iam.gserviceaccount.com`, roles `roles/aiplatform.user` and `roles/serviceusage.serviceUsageConsumer` on the project. No key exists (creation is blocked by an organisation policy, which was not touched); access is through Workload Identity Federation, see above |
| AWS IAM role and instance profile | `storybound-demo-role` and instance profile `storybound-demo-role` (no permissions policies, tagged Name=storybound-demo, Project=storybound), attached to the instance |
| Google workload identity pool and provider | `storybound-demo-pool`, provider `storybound-demo-aws` (project number 147606977567) |

Notes: the AMI was found with `ec2 describe-images` (owner Canonical) because `ssm:GetParameter` is not allowed for this IAM user. The Google service-account key was refused by an organisation policy. Nothing else was refused.

## How the server is set up

- Code: `git clone --depth 1 https://github.com/hatif03/storybound /opt/storybound` (commit 7f8e97d at install). Python 3.12 venv at `/opt/storybound/.venv`, installed with `pip install -e .`. Apt packages: python3.12, python3.12-venv, git, ffmpeg, curl, unzip and the Chrome shared libraries (libnss3, libgbm1, libasound2t64 and friends). For the movie: Node 22.11.0 from the official tarball in `/usr/local` (HyperFrames needs Node 22 or later; the apt Node 18 is still installed but comes later in PATH), and HyperFrames downloads its own chrome-headless-shell on first use into `/var/lib/storybound`.
- `web/dist` is not in git: it was built on the builder's machine (`cd web; npm run build`) and unpacked into `/opt/storybound/web/dist`. After a web change, rebuild locally, `tar czf dist.tgz dist`, `scp` it to the server and unpack into `/opt/storybound/web/`.
- User `storybound` (no login). The checkout is root-owned and read-only for the app; only `/opt/storybound/runs` (and its home `/var/lib/storybound`) are writable. The unit also sets `ProtectSystem=strict`, `NoNewPrivileges` and `PYTHONDONTWRITEBYTECODE=1`.
- `storybound.service`: `/opt/storybound/.venv/bin/python -m uvicorn storybound.api:app --app-dir src --host 0.0.0.0 --port 80`, port 80 through `CAP_NET_BIND_SERVICE`, `Restart=always`, secrets from `/etc/storybound/env` (root-owned, mode 600).
- `storybound-clean.timer` (hourly) runs `find /opt/storybound/runs -mindepth 1 -maxdepth 1 -mmin +1440 -exec rm -rf {} +`: nothing a visitor made stays more than about 24 hours (a visitor can also press Forget, which deletes at once).

### Settings in `/etc/storybound/env` (names only)

| Variable | Meaning |
| --- | --- |
| `IFM_API_KEY`, `IFM_BASE_URL` | K2 judge |
| `LITELLM_API_KEY`, `LITELLM_BASE_URL` | hackathon gateway (planner, quiz maker, picture check) |
| `GCP_PROJECT` | Google project for Vertex Gemini and Text-to-Speech |
| `GOOGLE_APPLICATION_CREDENTIALS` | `/etc/storybound/gcp-wif.json` (mode 640, root:storybound): the keyless credential config |
| `STORYBOUND_DAILY_STORIES=40` | at most 40 stories a day for all visitors together |
| `STORYBOUND_PER_IP_STORIES=3` | at most 3 stories a day per visitor address |
| `STORYBOUND_DAILY_VIDEOS=8` | at most 8 read-along movies a day |
| `STORYBOUND_MAX_RUNS=2` | at most 2 stories made at the same time (a third gets a calm "busy, try in a minute") |
| `STORYBOUND_MEDIA=1` | pictures and narration on |
| `PYTHONDONTWRITEBYTECODE=1` | keeps the checkout clean |

No `NEATLOGS_*` variables: tracing is off (`/api/health` shows `"tracing": false`).

## Operate

- Log in: `ssh -i C:\Users\mdhat\.ssh\storybound-demo.pem ubuntu@<public dns>`
- Logs: `sudo journalctl -u storybound -f`; status: `systemctl status storybound`
- Update code: `cd /opt/storybound && sudo git pull --ff-only && sudo /opt/storybound/.venv/bin/pip install -q -e . && sudo systemctl restart storybound` (restarting forgets stories in memory; running stories stop)
- Change a setting: `sudo nano /etc/storybound/env && sudo systemctl restart storybound`
- Check a real story, from your machine:
  ```
  U=http://<public dns>
  curl -s -X POST $U/api/stories -F fixture_id=benign/bunny-bow-carrot -F lesson_id=sharing -F pictures=auto
  curl -N $U/api/stories/<story_id>/events      # until run.finished or error
  curl -s $U/api/stories/<story_id>/receipt
  curl -s -X DELETE $U/api/stories/<story_id>   # forget it
  ```

## Cost

Estimate at us-east-1 list prices: t3.small about $0.50 a day, 20 GB gp3 about $0.05 a day, public IPv4 address about $0.12 a day: **about $0.70 a day (about $5 for a week)**, plus a few cents of traffic. Model costs are separate (Google and the hackathon gateway) and capped by the story limits above: a story costs about $0.20 to $0.40 (measured $0.21 with four pictures), plus about $0.04 for a movie, so the day caps bound it near $16 of Google spend if every slot were used; lower `STORYBOUND_DAILY_STORIES` to cut that. The team allowance is $25: stop the instance when judging is over.

## Shut down after the hackathon

Run with `AWS_PROFILE=neathack` and region `us-east-1`. Only the three things named here are ours.

```
# AWS (profile neathack, us-east-1)
aws ec2 terminate-instances --instance-ids i-0ffe97be19c22a88c --region us-east-1 --profile neathack
aws ec2 wait instance-terminated --instance-ids i-0ffe97be19c22a88c --region us-east-1 --profile neathack
aws ec2 delete-security-group --group-id sg-09e65b4a89aef1304 --region us-east-1 --profile neathack
aws ec2 delete-key-pair --key-name storybound-demo --region us-east-1 --profile neathack
aws iam remove-role-from-instance-profile --instance-profile-name storybound-demo-role --role-name storybound-demo-role --profile neathack
aws iam delete-instance-profile --instance-profile-name storybound-demo-role --profile neathack
aws iam delete-role --role-name storybound-demo-role --profile neathack
del C:\Users\mdhat\.ssh\storybound-demo.pem

# Google
P=project-f0b6b4ce-541f-43ff-9f7
SA=storybound-demo@$P.iam.gserviceaccount.com
gcloud iam workload-identity-pools providers delete storybound-demo-aws --workload-identity-pool=storybound-demo-pool --location=global --project $P
gcloud iam workload-identity-pools delete storybound-demo-pool --location=global --project $P
gcloud projects remove-iam-policy-binding $P --member serviceAccount:$SA --role roles/aiplatform.user
gcloud projects remove-iam-policy-binding $P --member serviceAccount:$SA --role roles/serviceusage.serviceUsageConsumer
gcloud iam service-accounts delete $SA --project $P        # also removes its workloadIdentityUser binding
# optional, if nothing else uses them:
# gcloud services disable iamcredentials.googleapis.com sts.googleapis.com --project $P
```

To only pause (stop paying for compute): `aws ec2 stop-instances --instance-ids i-0ffe97be19c22a88c` (the public DNS name will change on start).

## Privacy and limits, plainly

- http only: anything a visitor uploads travels unencrypted. Visitors should be told (the app does not say it yet) not to upload a real child's photo and to use a sample or a made-up drawing.
- Tracing is off on this server. Stories and drawings live only under `/opt/storybound/runs` and are deleted after 24 hours at the latest (or at once on Forget).
- Drawings and story text are sent to Google (Gemini, Text-to-Speech), the K2 judge and the hackathon gateway to make the story.
