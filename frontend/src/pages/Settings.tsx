import { useRef, useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { avatarUrl, changeMyPassword, updateMyProfile, uploadMyAvatar } from "../api/endpoints";
import { useAuth } from "../context/AuthContext";

function initials(name: string | undefined): string {
  if (!name) return "?";
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");
}

export default function Settings() {
  const { user, refreshUser } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [avatarError, setAvatarError] = useState<string | null>(null);
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);

  const [phone, setPhone] = useState(user?.phone_number ?? "");
  const [officeLocation, setOfficeLocation] = useState(user?.office_location ?? "");
  const [profileSaved, setProfileSaved] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSaved, setPasswordSaved] = useState(false);

  if (!user) return null;

  async function handleAvatarChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setAvatarError(null);
    setIsUploadingAvatar(true);
    try {
      await uploadMyAvatar(file);
      await refreshUser();
    } catch {
      setAvatarError("Could not upload image (PNG/JPEG/WEBP, under 3MB)");
    } finally {
      setIsUploadingAvatar(false);
    }
  }

  async function handleProfileSubmit(event: FormEvent) {
    event.preventDefault();
    setProfileError(null);
    setProfileSaved(false);
    try {
      await updateMyProfile({ phone_number: phone, office_location: officeLocation });
      await refreshUser();
      setProfileSaved(true);
    } catch {
      setProfileError("Could not save changes");
    }
  }

  async function handlePasswordSubmit(event: FormEvent) {
    event.preventDefault();
    setPasswordError(null);
    setPasswordSaved(false);
    if (newPassword !== confirmPassword) {
      setPasswordError("New password and confirmation don't match");
      return;
    }
    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters");
      return;
    }
    try {
      await changeMyPassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setPasswordSaved(true);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setPasswordError(detail ?? "Could not change password");
    }
  }

  return (
    <div className="settings-page">
      <h1>Settings</h1>

      <section className="settings-section">
        <h2>Profile photo</h2>
        <div className="avatar-row">
          <div className="avatar-preview">
            {user.avatar_url ? <img src={avatarUrl(user.id)} alt="" /> : <span>{initials(user.display_name)}</span>}
          </div>
          <div>
            <button type="button" onClick={() => fileInputRef.current?.click()} disabled={isUploadingAvatar}>
              {isUploadingAvatar ? "Uploading..." : "Upload photo"}
            </button>
            <input ref={fileInputRef} type="file" accept="image/png,image/jpeg,image/webp" hidden onChange={handleAvatarChange} />
            {avatarError && <p className="error">{avatarError}</p>}
          </div>
        </div>
      </section>

      <section className="settings-section">
        <h2>Account</h2>
        <form className="settings-form" onSubmit={handleProfileSubmit}>
          <label>
            Email <span className="hint-text">(fixed by admin)</span>
            <input value={user.email} disabled />
          </label>
          <label>
            Name <span className="hint-text">(fixed by admin)</span>
            <input value={user.display_name} disabled />
          </label>
          <label>
            Phone number
            <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+91 98765 43210" />
          </label>
          <label>
            Office location
            <input value={officeLocation} onChange={(e) => setOfficeLocation(e.target.value)} placeholder="Bengaluru, India" />
          </label>
          {profileError && <p className="error">{profileError}</p>}
          {profileSaved && <p className="success-text">Saved.</p>}
          <button type="submit">Save changes</button>
        </form>
      </section>

      <section className="settings-section">
        <h2>Change password</h2>
        <form className="settings-form" onSubmit={handlePasswordSubmit}>
          <label>
            Current password
            <input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
          </label>
          <label>
            New password
            <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={8} />
          </label>
          <label>
            Confirm new password
            <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required minLength={8} />
          </label>
          {passwordError && <p className="error">{passwordError}</p>}
          {passwordSaved && <p className="success-text">Password updated.</p>}
          <button type="submit">Update password</button>
        </form>
      </section>
    </div>
  );
}
