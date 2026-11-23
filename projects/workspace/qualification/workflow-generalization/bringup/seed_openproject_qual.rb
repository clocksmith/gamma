# Idempotent seeder for the isolated OpenProject qualification instance (clocksmith/deco#88).
# Creates the Stage2 statuses, roles, three projects, two local users and their API tokens.
# The user password comes from STAGE2_USER_PASSWORD; nothing secret is stored in this file.
# Run inside the application container: bundle exec rails runner /tmp/seed_openproject_qual.rb
require 'json'

STAGE2_PASSWORD = ENV.fetch('STAGE2_USER_PASSWORD')

unless Role.where(builtin: Role::BUILTIN_NON_MEMBER).exists?
  RootSeeder.new.seed_data! do |r|
    r.send(:seed_basic_data)
    r.send(:seed_admin_user)
  end
end

IssuePriority.find_or_create_by!(name: 'Stage2Normal') do |p|
  p.is_default = !IssuePriority.where(is_default: true).exists?
  p.active = true
end
unless IssuePriority.where(is_default: true).exists?
  IssuePriority.first.update!(is_default: true)
end

Status.where(is_default: true).update_all(is_default: false)
s_new = Status.find_or_create_by!(name: 'Stage2New')
s_new.update!(is_default: true, is_closed: false)
s_approved = Status.find_or_create_by!(name: 'Stage2Approved') { |s| s.is_closed = false }
s_hold = Status.find_or_create_by!(name: 'Stage2Hold') { |s| s.is_closed = false }
s_restricted = Status.find_or_create_by!(name: 'Stage2Disallowed') { |s| s.is_closed = true }

task_type = Type.where(is_default: true).first || Type.first || Type.create!(name: 'Stage2Task', is_default: true, color_id: nil)
task_type.update!(is_default: true)

perms = %i[
  view_project
  view_work_packages
  add_work_packages
  edit_work_packages
  add_work_package_notes
  manage_subtasks
]

author_role = ProjectRole.find_or_initialize_by(name: 'Stage2AuthorRole')
author_role.permissions = perms
author_role.save!

approver_role = ProjectRole.find_or_initialize_by(name: 'Stage2ApproverRole')
approver_role.permissions = perms
approver_role.save!

Workflow.where(type_id: task_type.id, role_id: [author_role.id, approver_role.id]).delete_all
[
  [s_new, s_new],
  [s_approved, s_approved],
  [s_hold, s_hold],
].each do |old_s, new_s|
  Workflow.create!(type_id: task_type.id, old_status_id: old_s.id, new_status_id: new_s.id, role_id: author_role.id)
end

[
  [s_new, s_approved],
  [s_new, s_hold],
  [s_approved, s_hold],
  [s_hold, s_approved],
  [s_approved, s_approved],
  [s_hold, s_hold],
  [s_new, s_new],
].each do |old_s, new_s|
  Workflow.create!(type_id: task_type.id, old_status_id: old_s.id, new_status_id: new_s.id, role_id: approver_role.id)
end

projects = [
  ['stage2-qual-proj', 'Stage 2 Qualification Project'],
  ['stage2-partner-proj', 'Stage 2 Partner Project'],
  ['stage2-quarantine-proj', 'Stage 2 Quarantine Intake'],
].map do |ident, title|
  p = Project.find_or_initialize_by(identifier: ident)
  p.name = title
  p.public = false
  p.active = true
  p.enabled_module_names = ['work_package_tracking']
  p.save!
  p.types = [task_type] unless p.types.include?(task_type)
  p
end
project = projects.first

def ensure_local_user(login, first, last)
  u = User.find_or_initialize_by(login: login)
  u.firstname = first
  u.lastname = last
  u.mail = "#{login}@local.invalid"
  u.admin = false
  u.language = 'en'
  u.status = Principal.statuses[:active]
  u.force_password_change = false if u.respond_to?(:force_password_change=)
  u.password = STAGE2_PASSWORD
  u.password_confirmation = STAGE2_PASSWORD
  u.save!
  u
end

u_author = ensure_local_user('stage2_author', 'Stage2', 'Author')
u_approver = ensure_local_user('stage2_approver', 'Stage2', 'Approver')

projects.each do |p|
  [[u_author, author_role], [u_approver, approver_role]].each do |usr, rl|
    m = Member.find_or_initialize_by(project_id: p.id, principal: usr)
    m.roles = [rl]
    m.save!
  end
end

Token::API.where(user_id: [u_author.id, u_approver.id]).delete_all
tok_author = Token::API.create!(user: u_author)
tok_approver = Token::API.create!(user: u_approver)

puts "STAGE2_SEED_JSON:" + JSON.generate({
  projectIdentifier: project.identifier,
  projectId: project.id,
  projectIdentifiers: projects.map(&:identifier),
  newStatusHref: "/api/v3/statuses/#{s_new.id}",
  approvedStatusHref: "/api/v3/statuses/#{s_approved.id}",
  holdStatusHref: "/api/v3/statuses/#{s_hold.id}",
  disallowedStatusHref: "/api/v3/statuses/#{s_restricted.id}",
  authorUserId: u_author.id,
  approverUserId: u_approver.id,
  authorToken: tok_author.plain_value,
  approverToken: tok_approver.plain_value,
})
